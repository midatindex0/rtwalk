import functools

from graphql.error import GraphQLError
from strawberry.types import Info


def authenticated(bot=True, system_override=True):
    def __dec(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            info: Info = kwargs.get("info")
            if not info:
                raise GraphQLError(
                    "Internal error (no context to verify authentication)",
                    extensions={"tp": "INTERNAL_ERROR"},
                )
            user = await info.context.user()
            if not user:
                raise GraphQLError(
                    "Unauthenticated request",
                    extensions={"tp": "UNAUTHENTICATED_REQUEST"},
                )
            if not bot and user.bot:
                if user.username != "system":
                    raise GraphQLError(
                        "Bots cannot use this endpoint",
                        extensions={"tp": "PERMISSION_DENIED"},
                    )
                elif not system_override:
                    raise GraphQLError(
                        "Syatem cannot use this endpoint",
                        extensions={"tp": "PERMISSION_DENIED"},
                    )
            return await fn(*args, **kwargs)

        return wrapper

    return __dec
