from time import time
from typing import Optional, List

import strawberry
from beanie import Document, Indexed
from beanie.odm.fields import PydanticObjectId
from pydantic import Field

from models.file import File


@strawberry.type
class Forum:
    id: str
    name: str
    display_name: str
    description: Optional[str] = None
    icon: Optional[File] = None
    banner: Optional[File] = None
    created_at: int
    modified_at: int
    owner_id: str


class DBComment(Document):
    content: Optional[str] = None
    commenter_id: PydanticObjectId
    parent_id: PydanticObjectId
    created_at: int = Field(default_factory=lambda: int(time()))
    modified_at: int = Field(default_factory=lambda: int(time()))
    upvotes: int = 0
    downvotes: int = 0
    upvoted_by: List[PydanticObjectId] = Field(default=[])
    downvoted_by: List[PydanticObjectId] = Field(default=[])


class DBPost(Document):
    title: str
    tags: Optional[List[str]] = None
    content: Optional[str] = None
    attachments: Optional[List[File]] = None
    created_at: int = Field(default_factory=lambda: int(time()))
    modified_at: int = Field(default_factory=lambda: int(time()))
    poster_id: PydanticObjectId
    upvotes: int = 0
    downvotes: int = 0
    upvoted_by: List[PydanticObjectId] = Field(default=[])
    downvoted_by: List[PydanticObjectId] = Field(default=[])
    comments: List[DBComment] = Field(default=[])


class DBForum(Document):
    name: Indexed(str, unique=True)
    display_name: str
    description: Optional[str] = None
    icon: Optional[File] = None
    banner: Optional[File] = None
    created_at: int = Field(default_factory=lambda: int(time()))
    modified_at: int = Field(default_factory=lambda: int(time()))
    owner_id: PydanticObjectId
    moderators: List[PydanticObjectId] = Field(default=[])
    banned_members: List[PydanticObjectId] = Field(default=[])
    posts: List[DBPost] = Field(default=[])

    def gql(self) -> Forum:
        return Forum(
            id=str(self.id),
            name=str(self.name),
            display_name=self.display_name,
            description=self.description,
            icon=self.icon,
            banner=self.banner,
            created_at=self.created_at,
            modified_at=self.modified_at,
            owner_id=self.owner_id,
        )
