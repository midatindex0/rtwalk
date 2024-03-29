from time import time
from typing import List, Optional

import strawberry
from beanie import Document
from beanie.odm.fields import PydanticObjectId
from pydantic import BaseModel, Field

from models.file import File


@strawberry.type
class Poll(BaseModel):
    options: List[str]
    results: List[int]
    participants: List[List[str]]


class DBPoll(BaseModel):
    options: List[str]
    results: List[int]
    participants: List[List[PydanticObjectId]]


@strawberry.type
class Post:
    id: str
    title: str
    tags: Optional[List[str]]
    content: Optional[str]
    attachments: Optional[List[File]]
    poll: Optional[Poll]
    comment_count: int
    participants: List[str]
    created_at: int
    modified_at: int
    poster_id: str
    forum_id: str
    upvotes: int
    downvotes: int
    upvoted_by: List[str]
    downvoted_by: List[str]
    pinned: bool
    rolling: bool


class DBPost(Document):
    title: str
    tags: Optional[List[str]] = None
    content: Optional[str] = None
    attachments: Optional[List[File]] = None
    poll: Optional[DBPoll] = None
    comment_count: int = 0
    participants: List[PydanticObjectId] = Field(default=[])
    created_at: int = Field(default_factory=lambda: int(time()))
    modified_at: int = Field(default_factory=lambda: int(time()))
    poster_id: PydanticObjectId
    forum_id: PydanticObjectId
    upvotes: int = 0
    downvotes: int = 0
    upvoted_by: List[PydanticObjectId] = Field(default=[])
    downvoted_by: List[PydanticObjectId] = Field(default=[])
    pinned: bool = False
    rolling: bool = False

    def gql(self) -> Post:
        return Post(
            id=str(self.id),
            title=self.title,
            tags=self.tags,
            content=self.content,
            attachments=self.attachments,
            poll=(
                Poll(
                    options=self.poll.options,
                    results=self.poll.results,
                    participants=list(
                        map(lambda l: map(str, l), self.poll.participants)
                    ),
                )
                if self.poll
                else None
            ),
            comment_count=self.comment_count,
            participants=list(map(str, self.participants)),
            created_at=self.created_at,
            modified_at=self.modified_at,
            poster_id=self.poster_id,
            forum_id=self.forum_id,
            upvotes=self.upvotes,
            downvotes=self.downvotes,
            upvoted_by=list(map(str, self.upvoted_by)),
            downvoted_by=list(map(str, self.downvoted_by)),
            pinned=self.pinned,
            rolling=self.rolling,
        )
