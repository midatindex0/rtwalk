import dotenv

dotenv.load_dotenv()

import os
from contextlib import asynccontextmanager

import strawberry
from aiocache import Cache
from aiocache.serializers import PickleSerializer
from argon2 import PasswordHasher
from beanie import init_beanie
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from strawberry.fastapi import BaseContext, GraphQLRouter

from gql import users
from models.user import DBUser, User, UserSecret

MAJOR_V = 0
MINOR_v = 0
BUG_FIX_V = 0

ph = PasswordHasher()
pending = Cache(
    Cache.REDIS,
    endpoint="127.0.0.1",
    serializer=PickleSerializer(),
    port=6379,
    namespace="email_verify",
    ttl=10 * 60,
)
session = Cache(
    Cache.REDIS,
    endpoint="127.0.0.1",
    port=6379,
    namespace="auth_session",
    ttl=15 * 24 * 60 * 60,
)
email_cipher = Fernet(os.getenv("EMAIL_CIPHER_KEY").encode())
session_cipher = ChaCha20Poly1305(bytes.fromhex(os.getenv("AUTH_KEY")))
scrypt = Scrypt(
    salt=os.getenv("EMAIL_HASH_SALT").encode(), length=32, n=2**14, r=8, p=1
)


class Ctx(BaseContext):
    def __init__(self):
        self.argon2 = ph
        self.pending = pending
        self.session = session
        self.email_cipher = email_cipher
        self.session_cipher = session_cipher
        self.email_hasher = scrypt

    async def user(self) -> User | None:
        if not self.request:
            return None

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
        return user


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

    @strawberry.field
    def version(self) -> Version:
        return Version()


@strawberry.type
class Mutation:
    create_user = strawberry.field(resolver=users.create_user)
    verify_user = strawberry.field(resolver=users.verify_user)
    login = strawberry.field(resolver=users.login)


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema, context_getter=lambda: Ctx())


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncIOMotorClient(os.getenv("DB_URL"))
    await init_beanie(database=client.rtwalk_py, document_models=[DBUser, UserSecret])
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(graphql_app, prefix="/graphql")
