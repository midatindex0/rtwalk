import dotenv

dotenv.load_dotenv()

import os
from contextlib import asynccontextmanager
from typing import Optional

import opendal
import strawberry
import uvicorn
from aiocache import Cache
from aiocache.serializers import PickleSerializer
from argon2 import PasswordHasher
from beanie import init_beanie
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from strawberry.fastapi import BaseContext, GraphQLRouter

from consts import CDN_ROUTE, ORIGINS
from gql import comments, files, forums, posts, users
from models.comment import DBComment
from models.forum import DBForum
from models.post import DBPost
from models.user import DBUser, User, UserSecret

MAJOR_V = 0
MINOR_v = 0
BUG_FIX_V = 0

ph = PasswordHasher()
pending = Cache(
    Cache.REDIS,
    endpoint=os.getenv("REDIS_ENDPOINT"),
    serializer=PickleSerializer(),
    port=int(os.getenv("REDIS_PORT")),
    namespace="email_verify",
    ttl=10 * 60,
)
session = Cache(
    Cache.REDIS,
    endpoint=os.getenv("REDIS_ENDPOINT"),
    port=int(os.getenv("REDIS_PORT")),
    namespace="auth_session",
    ttl=15 * 24 * 60 * 60,
)
email_cipher = Fernet(os.getenv("EMAIL_CIPHER_KEY").encode())
session_cipher = ChaCha20Poly1305(bytes.fromhex(os.getenv("AUTH_KEY")))
op = opendal.AsyncOperator("fs", root="data/")


class Ctx(BaseContext):
    def __init__(self):
        self.argon2 = ph
        self.pending = pending
        self.session = session
        self.email_cipher = email_cipher
        self.session_cipher = session_cipher
        self.email_hasher = scrypt = Scrypt(
            salt=os.getenv("EMAIL_HASH_SALT").encode(), length=32, n=2**14, r=8, p=1
        )
        self.op = op
        self.session_user = None

    async def user(self) -> Optional[User]:
        if not self.request:
            return None

        if self.session_user:
            return self.session_user

        session_token = self.request.cookies.get("session")
        if not session_token:
            return None
        try:
            token, nonce = session_token.split(";")
            uuid = self.session_cipher.decrypt(
                bytes.fromhex(nonce), bytes.fromhex(token), None
            ).decode()
            user = User(**(await self.session.get(uuid)))
        except:
            return None
        self.session_user = user
        return user

    async def logout(self):
        if not self.request:
            return

        session_token = self.request.cookies.get("session")
        if not session_token:
            return
        try:
            token, nonce = session_token.split(";")
            uuid = self.session_cipher.decrypt(
                bytes.fromhex(nonce), bytes.fromhex(token), None
            ).decode()
            user = User(**(await self.session.get(uuid)))
            sessions = await self.session.get(user.id)
            sessions.remove(uuid)
            if sessions:
                sessions = await self.session.set(user.id, sessions)
            else:
                await self.session.delete(user.id)
            await self.session.delete(uuid)
        except:
            return
        self.session_user = None


@strawberry.type
class Version:
    major: int
    minor: int
    bug_fix: int

    def __init__(self):
        self.major = MAJOR_V
        self.minor = MINOR_v
        self.bug_fix = BUG_FIX_V

    @strawberry.field
    def version_string(self) -> str:
        return f"{self.major}.{self.minor}.{self.bug_fix}"


@strawberry.type
class Query:
    me = strawberry.field(resolver=users.me)
    get_user = strawberry.field(resolver=users.get_user)
    get_users = strawberry.field(resolver=users.get_users)
    get_forum = strawberry.field(resolver=forums.get_forum)
    get_forums = strawberry.field(resolver=forums.get_forums)
    get_post = strawberry.field(resolver=posts.get_post)
    get_posts = strawberry.field(resolver=posts.get_posts)
    get_comment = strawberry.field(resolver=comments.get_comment)
    get_comments = strawberry.field(resolver=comments.get_comments)

    @strawberry.field
    def version(self) -> Version:
        return Version()


@strawberry.type
class Mutation:
    create_user = strawberry.field(resolver=users.create_user)
    create_bot = strawberry.field(resolver=users.create_bot)
    verify_user = strawberry.field(resolver=users.verify_user)
    login = strawberry.field(resolver=users.login)
    logout = strawberry.field(resolver=users.logout)
    create_forum = strawberry.field(resolver=forums.create_forum)
    create_post = strawberry.field(resolver=posts.create_post)
    create_comment = strawberry.field(resolver=comments.create_commment)
    upload_files = strawberry.field(resolver=files.upload_files)


# @strawberry.type
# class Subscription:
#     post_creation_event = strawberry.subscription(
#         resolver=subscriptions.post_creation_event
#     )


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema, context_getter=lambda: Ctx())


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncIOMotorClient(os.getenv("DB_URL"))
    await init_beanie(
        database=client.rtwalk_py,
        document_models=[DBUser, UserSecret, DBForum, DBPost, DBComment],
    )
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(graphql_app, prefix="/api/v1")

app.mount(CDN_ROUTE, StaticFiles(directory="data"), name="cdn")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=3758, workers=1)
