from time import time
from typing import List, Optional

import strawberry
from beanie import Document
from beanie.odm.fields import PydanticObjectId
from pydantic import Field


@strawberry.type
class Comment:
    content: str
    commenter_id: str
    reply_to: Optional[str]
    post_id: str
    created_at: int
    modified_at: int
    upvotes: int
    downvotes: int
    upvoted_by: List[str]
    downvoted_by: List[str]


class DBComment(Document):
    content: str
    commenter_id: PydanticObjectId
    reply_to: Optional[PydanticObjectId] = None
    post_id: PydanticObjectId
    created_at: int = Field(default_factory=lambda: int(time()))
    modified_at: int = Field(default_factory=lambda: int(time()))
    upvotes: int = 0
    downvotes: int = 0
    upvoted_by: List[PydanticObjectId] = Field(default=[])
    downvoted_by: List[PydanticObjectId] = [Field(default=[])]
