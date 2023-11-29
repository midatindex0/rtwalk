import decorator
from graphql.error import GraphQLError
from strawberry.types import Info


@decorator.decorator
async def authenticated(fn, info: Info):
    if await info.context.user():
        return await fn(info)
    raise GraphQLError(
        "Unauthenticated request", extensions={"tp": "UNAUTHENTICATED_REQUEST"}
    )
