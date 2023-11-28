import os
import random
from hmac import compare_digest

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from strawberry.types import Info
from zxcvbn import zxcvbn

from error import UserCreationError, UsercReationErrorType
from gql import Ok
from models.user import DBUser, User

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


async def create_user(username: str, email: str, password: str, info: Info) -> Ok:
    """
    Can fail: Check UserCreationErrorType for error types. Error extension is set as `tp`.
    """
    r = zxcvbn(password, user_inputs=[username, email])
    if r["score"] < 3:
        raise UserCreationError(
            f"Password is too weak [{r['score']}/4]",
            tp=UsercReationErrorType.WEAK_PASSWORD,
        ).into()
    if len(username) < 3:
        raise UserCreationError(
            f"Username must be atlest 3 characters",
            tp=UsercReationErrorType.USERNAME_TOO_SHORT,
        ).into()
    # TODO: Check invalid character
    u = await DBUser.find_one(DBUser.username == username)
    if u:
        raise UserCreationError(
            f"Username already exists",
            tp=UsercReationErrorType.USERNAME_ALREADY_EXISTS,
        ).into()

    # Silently drop if email exists
    u = await DBUser.find_one(DBUser.email == email)
    if u:
        return Ok(msg="Check your email")

    code = random.randint(10000, 99999)
    user = DBUser(
        username=username,
        email=email,
        password=info.context.ph.hash(password),
        display_name=username,
    )

    await info.context.pending.set(username, [code, user, 0])
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


async def verify_user(username: str, code: int, info: Info) -> User:
    try:
        ccode, user, attempts = await info.context.pending.get(username)
    except:
        raise UserCreationError(
            f"Your code expired. Register again",
            tp=UsercReationErrorType.CODE_EXPIRED,
        ).into()
    if attempts == 3:
        del info.context.pending[username]
        raise UserCreationError(
            f"Your code expired. Register again",
            tp=UsercReationErrorType.CODE_EXPIRED,
        ).into()
    if not compare_digest(str(code), str(ccode)):
        await info.context.pending.set(username, [code, user, attempts + 1])
        raise UserCreationError(
            f"Incorrect code",
            tp=UsercReationErrorType.INCORRECT_CODE,
        ).into()
    await info.context.pending.delete(username)
    await user.insert()
    return user.gql()


async def login(email: str, password: str) -> None:
    pass
