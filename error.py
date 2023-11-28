from enum import Enum

from graphql.error import GraphQLError
import strawberry


@strawberry.enum
class UsercReationErrorType(Enum):
    WEAK_PASSWORD = "WEAK_PASSOWRD"
    USERNAME_TOO_SHORT = "USERNAME_TOO_SHORT"
    USERNAME_ALREADY_EXISTS = "USERNAME_ALREADY_EXISTS"
    INCORRECT_CODE = 3
    CODE_EXPIRED = 4


@strawberry.type
class UserCreationError(Exception):
    def __init__(self, *args, tp: UsercReationErrorType):
        super().__init__(*args)
        self.msg = args[0]
        self.tp = tp

    def into(self) -> GraphQLError:
        return GraphQLError(self.msg, extensions={"tp": self.tp.name})
