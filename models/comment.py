from __future__ import annotations
from time import time
from typing import List, Optional, Annotated

import strawberry
from beanie import Document, Link
from beanie.odm.fields import PydanticObjectId
from pydantic import Field

from models.user import User, DBUser


@strawberry.type
class Comment:
    id: str
    content: str
    commenter_id: str
    reply_to: Optional[str]
    post_id: str
    forum_id: str
    commenter: Annotated[User, strawberry.lazy(".user")]
    created_at: int
    modified_at: int
    reply_count: int
    upvotes: int
    downvotes: int
    upvoted_by: List[str]
    downvoted_by: List[str]


class DBComment(Document):
    content: str
    commenter_id: PydanticObjectId
    reply_to: Optional[PydanticObjectId] = None
    post_id: PydanticObjectId
    forum_id: PydanticObjectId
    commenter: Optional[Link[DBUser]] = None  # Createtion guarrentes it to be populated
    created_at: int = Field(default_factory=lambda: int(time()))
    modified_at: int = Field(default_factory=lambda: int(time()))
    reply_count: int = 0
    upvotes: int = 0
    downvotes: int = 0
    upvoted_by: List[PydanticObjectId] = Field(default=[])
    downvoted_by: List[PydanticObjectId] = Field(default=[])

    def gql(self) -> Comment:
        return Comment(
            id=str(self.id),
            content=self.content,
            commenter_id=str(self.commenter_id),
            reply_to=str(self.reply_to) if self.reply_to else None,
            post_id=str(self.post_id),
            forum_id=str(self.forum_id),
            commenter=self.commenter.gql(),
            created_at=self.created_at,
            modified_at=self.modified_at,
            reply_count=self.reply_count,
            upvoted_by=list(map(str, self.upvoted_by)),
            downvoted_by=list(map(str, self.downvoted_by)),
            upvotes=self.upvotes,
            downvotes=self.downvotes,
        )
