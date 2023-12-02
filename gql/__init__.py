from enum import Enum
from typing import Generic, List, TypeVar, Optional

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
    CREATED_AT_DESC = 0


@strawberry.type
class BotCreds:
    token: str


T = TypeVar("T")


@strawberry.type
class Page(Generic[T]):
    total: int
    next_page: Optional[int]
    items: List[T]
