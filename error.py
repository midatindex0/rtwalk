from enum import Enum

import strawberry
from graphql.error import GraphQLError


@strawberry.enum
class UserCreationErrorType(Enum):
    WEAK_PASSWORD = "WEAK_PASSOWRD"
    INVALID_USERNAME = "USERNAME_TOO_SHORT"
    USERNAME_ALREADY_EXISTS = "USERNAME_ALREADY_EXISTS"
    INCORRECT_CODE = 3
    CODE_EXPIRED = 4
    UNSATISFIED_REQUIREMENTS = 5
    INVALID_EMAIL = 6


@strawberry.type
class UserCreationError(Exception):
    def __init__(self, *args, tp: UserCreationErrorType):
        super().__init__(*args)
        self.msg = args[0]
        self.tp = tp

    def into(self) -> GraphQLError:
        return GraphQLError(self.msg, extensions={"tp": self.tp.name})


@strawberry.type
class InvalidCredentials(Exception):
    def __init__(self):
        super().__init__()

    def gql(self) -> GraphQLError:
        return GraphQLError(
            "Invalid credentials", extensions={"tp": "INVALID_CREDENTIALS"}
        )


@strawberry.type
class InvalidGetQuery(Exception):
    def __init__(self):
        super().__init__()

    def gql(self) -> GraphQLError:
        return GraphQLError(
            "Invalid get query field input",
            extensions={"tp": "INVALID_GET_QUERY_INPUTS"},
        )


@strawberry.enum
class ForumCreationErrorType(Enum):
    INVALID_NAME = 0
    FORUM_ALREADY_EXISTS = 1


@strawberry.type
class ForumCreationError(Exception):
    def __init__(self, *args, tp: ForumCreationErrorType):
        super().__init__(*args)
        self.msg = args[0]
        self.tp = tp

    def into(self) -> GraphQLError:
        return GraphQLError(self.msg, extensions={"tp": self.tp.name})


@strawberry.enum
class PostCreationErrorType(Enum):
    FORUM_NOT_FOUND = 0
    LOCKED_FORUM = 0


@strawberry.type
class PostCreationError(Exception):
    def __init__(self, *args, tp: PostCreationErrorType):
        super().__init__(*args)
        self.msg = args[0]
        self.tp = tp

    def into(self) -> GraphQLError:
        return GraphQLError(self.msg, extensions={"tp": self.tp.name})
