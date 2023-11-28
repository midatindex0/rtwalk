import dotenv

dotenv.load_dotenv()

from contextlib import asynccontextmanager
import os
from functools import cached_property

import strawberry
from strawberry.asgi import GraphQL
from strawberry.fastapi import GraphQLRouter, BaseContext
from fastapi import FastAPI, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from argon2 import PasswordHasher
from aiocache import Cache
from aiocache.serializers import PickleSerializer

from models.user import DBUser
from gql import users

MAJOR_V = 0
MINOR_v = 0
BUG_FIX_V = 0


class Ctx(BaseContext):
    def __init__(self):
        self.ph = PasswordHasher()
        self.pending = Cache(
            Cache.REDIS,
            endpoint="127.0.0.1",
            serializer=PickleSerializer(),
            port=6379,
            namespace="email_verify",
            ttl=600,
        )


ctx = Ctx()


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
    @strawberry.field
    def version(self) -> Version:
        return Version()


@strawberry.type
class Mutation:
    create_user = strawberry.field(resolver=users.create_user)
    verify_user = strawberry.field(resolver=users.verify_user)


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema, context_getter=lambda: ctx)


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncIOMotorClient(os.getenv("DB_URL"))
    await init_beanie(database=client.rtwalk_py, document_models=[DBUser])
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(graphql_app, prefix="/graphql")
