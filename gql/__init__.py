from enum import Enum
from typing import Generic, List, Optional, TypeVar

import strawberry


@strawberry.type
class Ok:
    msg: str


@strawberry.enum
class UserSort(Enum):
    CREATED_AT_ASC = 0
    CREATED_AT_DESC = 1


@strawberry.enum
class ForumSort(Enum):
    CREATED_AT_ASC = 0
    CREATED_AT_DESC = 1


@strawberry.enum
class PostSort(Enum):
    CREATED_AT_ASC = 0
    CREATED_AT_DESC = 1
    PINNED = 2
    UPVOTES = 3
    DOWNVOTES = 4
    MODIFIED_AT_ASC = 5
    MODIFIED_AT_DESC = 6


@strawberry.enum
class CommentSort(Enum):
    CREATED_AT_ASC = 0
    CREATED_AT_DESC = 1
    PINNED = 2
    UPVOTES = 3
    DOWNVOTES = 4


@strawberry.type
class BotCreds:
    token: str


T = TypeVar("T")


@strawberry.type
class Page(Generic[T]):
    total: int
    next_page: Optional[int]
    items: List[T]
