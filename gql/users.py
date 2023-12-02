import os
import random
import re
import secrets
import string
from hmac import compare_digest
from typing import List
from uuid import uuid4

import argon2
from aiocache import Cache, cached
from aiocache.serializers import PickleSerializer
from beanie.odm.fields import PydanticObjectId
from beanie.operators import In
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from strawberry.types import Info
from zxcvbn import zxcvbn

from auth import authenticated
from error import InvalidCredentials, UserCreationError, UserCreationErrorType
from gql import BotCreds, Ok, Page, UserSort
from models.user import DBUser, User, UserSecret

DEV = os.getenv("DEV")


if not DEV:
    conf = ConnectionConfig(
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
        MAIL_FROM=os.getenv("MAIL_FROM"),
        MAIL_PORT=int(os.getenv("MAIL_PORT")),
        MAIL_SERVER=os.getenv("MAIL_SERVER"),
        MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME"),
        TEMPLATE_FOLDER="templates/",
        MAIL_STARTTLS=False,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )

email_regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
username_regex = r"^(?=.*[a-z])[a-z0-9_]+$"


async def create_user(username: str, email: str, password: str, info: Info) -> Ok:
    """
    Can fail: Check UserCreationErrorType for error types. Error extension is set as `tp`.
    """
    if not re.match(username_regex, username):
        raise UserCreationError(
            f"Username can only have lower case letters, numbers and underscore",
            tp=UserCreationErrorType.INVALID_USERNAME,
        ).into()
    if len(username) < 4:
        raise UserCreationError(
            f"Username must be atlest 4 characters",
            tp=UserCreationErrorType.INVALID_USERNAME,
        ).into()
    if not re.fullmatch(email_regex, email):
        raise UserCreationError(
            f"Invalid email address",
            tp=UserCreationErrorType.INVALID_EMAIL,
        ).into()
    r = zxcvbn(password, user_inputs=[username, email])
    if r["score"] < 4:
        raise UserCreationError(
            f"Password is too weak [{r['score']}/4]",
            tp=UserCreationErrorType.WEAK_PASSWORD,
        ).into()
    u = await DBUser.find_one(DBUser.username == username)
    if u:
        raise UserCreationError(
            f"Username already exists",
            tp=UserCreationErrorType.USERNAME_ALREADY_EXISTS,
        ).into()

    # hash email
    email_hash = info.context.email_hasher.derive(email.encode())
    # Silently drop if email exists
    u = await UserSecret.find_one(UserSecret.email_hash == email_hash)
    if u:
        return Ok(msg="Check your email")
    ect = info.context.email_cipher.encrypt(email.encode())

    code = random.randint(10000, 99999)
    user = DBUser(
        username=username,
        display_name=username,
    )
    user_secret = UserSecret(
        email=ect,
        email_hash=email_hash,
        password=info.context.email_cipher.encrypt(
            info.context.argon2.hash(password).encode()
        ),
    )

    await info.context.pending.set(username, [code, user, user_secret, 0])
    if not DEV:
        message = MessageSchema(
            subject="Verify Your Email",
            recipients=[email],
            template_body={"code": code, "username": username},
            subtype=MessageType.html,
        )
        fm = FastMail(conf)
        await fm.send_message(message, template_name="email_verify.html")
    else:
        return Ok(msg=f"{code}")

    return Ok(msg="Check your email")


alphabet = (string.ascii_letters + string.digits + string.punctuation).replace("@", "")


@authenticated(bot=False)
async def create_bot(info: Info, username: str) -> BotCreds:
    if not re.match(username_regex, username):
        raise UserCreationError(
            f"Username can only have lower case letters, numbers and underscore",
            tp=UserCreationErrorType.INVALID_USERNAME,
        ).into()
    if len(username) < 4:
        raise UserCreationError(
            f"Username must be atlest 4 characters",
            tp=UserCreationErrorType.INVALID_USERNAME,
        ).into()
    if len(username) < 4:
        raise UserCreationError(
            f"Username must be atlest 4 characters",
            tp=UserCreationErrorType.USERNAME_TOO_SHORT,
        ).into()
    # TODO: Check invalid character
    u = await DBUser.find_one(DBUser.username == username)
    if u:
        raise UserCreationError(
            f"Username already exists",
            tp=UserCreationErrorType.USERNAME_ALREADY_EXISTS,
        ).into()

    email = str(PydanticObjectId())
    password = "".join(secrets.choice(alphabet) for i in range(20))
    ect = info.context.email_cipher.encrypt(email.encode())
    email_hash = info.context.email_hasher.derive(email.encode())

    bot = DBUser(username=username, display_name=username, bot=True, bot_owner=owner.id)
    await bot.insert()
    user_secret = UserSecret(
        email=ect,
        email_hash=email_hash,
        password=info.context.email_cipher.encrypt(
            info.context.argon2.hash(password).encode()
        ),
        user_id=bot.id,
    )
    await user_secret.insert()
    return BotCreds(token=f"{email}@{password}")


async def verify_user(username: str, code: int, info: Info) -> User:
    try:
        ccode, user, user_secret, attempts = await info.context.pending.get(username)
    except:
        raise UserCreationError(
            f"Your code expired. Register again",
            tp=UserCreationErrorType.CODE_EXPIRED,
        ).into()
    if attempts == 3:
        await info.context.pending.delete(username)
        raise UserCreationError(
            f"Your code expired. Register again",
            tp=UserCreationErrorType.CODE_EXPIRED,
        ).into()
    if not compare_digest(str(code), str(ccode)):
        await info.context.pending.set(
            username, [code, user, user_secret, attempts + 1]
        )
        raise UserCreationError(
            f"Incorrect code",
            tp=UserCreationErrorType.INCORRECT_CODE,
        ).into()
    await info.context.pending.delete(username)
    await user.insert()
    user_secret.user_id = user.id
    await user_secret.insert()
    return user.gql()


async def login(email: str, password: str, info: Info) -> User:
    u = await info.context.user()
    if u:
        return u
    email_hash = info.context.email_hasher.derive(email.encode())
    user_secret = await UserSecret.find_one(UserSecret.email_hash == email_hash)
    if not user_secret:
        raise InvalidCredentials().gql()
    user_email = info.context.email_cipher.decrypt(user_secret.email).decode()
    if not compare_digest(user_email, email):
        raise InvalidCredentials().gql()
    try:
        if info.context.argon2.verify(
            info.context.email_cipher.decrypt(user_secret.password), password
        ):
            user = await DBUser.find_one(DBUser.id == user_secret.user_id)
            uuid = uuid4()
            nonce = os.urandom(12)
            cookie = f"{info.context.session_cipher.encrypt(nonce, str(uuid).encode(), None).hex()};{nonce.hex()}"
            await info.context.session.set(str(uuid), user.gql().__dict__)
            info.context.response.set_cookie(key="session", value=cookie)
            return user
    except argon2.exceptions.VerifyMismatchError:
        raise InvalidCredentials().gql()


@authenticated()
async def me(info: Info) -> User:
    return await info.context.user()


@cached(
    ttl=30,
    cache=Cache.REDIS,
    key="get_user",
    serializer=PickleSerializer(),
    port=6379,
    namespace="fn_cache",
)
async def get_user(id: str | None = None, username: str | None = None) -> User | None:
    if id:
        user = await DBUser.find_one(DBUser.id == PydanticObjectId(id))
        return user.gql() if user else None
    if username:
        user = await DBUser.find_one(DBUser.username == username)
        return user.gql() if user else None


@cached(
    ttl=10,
    cache=Cache.REDIS,
    key="get_users",
    serializer=PickleSerializer(),
    port=6379,
    namespace="fn_cache",
)
async def get_users(
    info: Info,
    ids: None | List[str] = None,
    usernames: None | List[str] = None,
    search: str | None = None,
    bot: bool | None = None,
    admin: bool | None = None,
    created_after: int | None = None,
    created_before: int | None = None,
    sort: UserSort | None = None,
    page: int = 1,
    limit: int = 10,
) -> Page[User]:
    if ids:
        ids = [*map(PydanticObjectId, ids)]
        users = DBUser.find(In(DBUser.id, ids))
    elif usernames:
        users = DBUser.find(In(DBUser.username, usernames))
    elif search:
        users = DBUser.find_all().aggregate(
            [
                {
                    "$search": {
                        "index": "users",
                        "text": {
                            "query": search,
                            "path": ["username", "display_name", "bio"],
                            "fuzzy": {},
                        },
                    }
                }
            ],
            projection_model=DBUser,
        )
    else:
        users = DBUser.find_all()
    if isinstance(bot, bool):
        users.find(DBUser.bot == bot)
    if isinstance(admin, bool):
        users.find(DBUser.admin == admin)
    if created_after:
        users.find(DBUser.created_at > created_after)
    if created_before:
        users.find(DBUser.created_at < created_before)
    if sort:
        match sort:
            case UserSort.CREATED_AT_ASC:
                users.sort(+DBUser.created_at)
            case UserSort.CREATED_AT_DESC:
                users.sort(-DBUser.created_at)
    total = 0
    for selection in info.selected_fields:
        if selection.name == "getUsers":
            for field in selection.selections:
                if field.name == "total":
                    total = await users.count()
                    break

    limit = min(20, limit)
    users.skip(limit * (page - 1)).limit(limit)
    users = await users.to_list()

    return Page(
        total=total,
        next_page=page + 1 if len(users) == limit else None,
        items=[*map(DBUser.gql, users)],
    )
