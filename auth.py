import decorator
from graphql.error import GraphQLError
from strawberry.types import Info


@decorator.decorator
async def authenticated(fn, info: Info, *args, **kwargs):
    if await info.context.user():
        return await fn(info, *args, **kwargs)
    raise GraphQLError(
        "Unauthenticated request", extensions={"tp": "UNAUTHENTICATED_REQUEST"}
    )
