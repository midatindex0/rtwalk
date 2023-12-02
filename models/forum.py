from time import time
from typing import List, Optional

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
    description: Optional[str]
    icon: Optional[File]
    banner: Optional[File]
    post_count: int
    created_at: int
    modified_at: int
    owner_id: str
    moderators: List[str]
    banned_members: List[str]
    locked: bool


class DBForum(Document):
    name: Indexed(str, unique=True)
    display_name: str
    description: Optional[str] = None
    icon: Optional[File] = None
    banner: Optional[File] = None
    post_count: int = 0
    created_at: int = Field(default_factory=lambda: int(time()))
    modified_at: int = Field(default_factory=lambda: int(time()))
    owner_id: PydanticObjectId
    moderators: List[PydanticObjectId] = Field(default=[])
    banned_members: List[PydanticObjectId] = Field(default=[])
    locked: bool = False

    def gql(self) -> Forum:
        return Forum(
            id=str(self.id),
            name=str(self.name),
            display_name=self.display_name,
            description=self.description,
            icon=self.icon,
            banner=self.banner,
            post_count=self.post_count,
            created_at=self.created_at,
            modified_at=self.modified_at,
            owner_id=self.owner_id,
            moderators=list(map(str, self.moderators)),
            banned_members=list(map(str, self.banned_members)),
            locked=self.locked,
        )
