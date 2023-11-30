from enum import Enum
from typing import Generic, List, TypeVar

import strawberry


@strawberry.type
class Ok:
    msg: str


@strawberry.enum
class UserSort(Enum):
    CREATED_AT_ASC = 0
    CREATED_AT_DESC = 0


T = TypeVar("T")


@strawberry.type
class Page(Generic[T]):
    total: int
    next_page: int | None
    items: List[T]
