from time import time
from typing import Optional, List

import strawberry
from beanie import Document, Indexed
from beanie.odm.fields import PydanticObjectId
from pydantic import Field

from models.file import File


@strawberry.type
class User:
    id: str
    username: str
    display_name: str
    bio: Optional[str] = None
    pfp: Optional[File] = None
    banner: Optional[File] = None
    stars: int = 0
    starred_by: List[str]
    created_at: int
    modified_at: int
    admin: bool = False
    bot: bool = False


class UserSecret(Document):
    user_id: PydanticObjectId | None = Field(default=None)
    email_hash: Indexed(bytes, unique=True)
    email: bytes
    password: bytes


class DBUser(Document):
    username: Indexed(str, unique=True)
    display_name: str
    bio: Optional[str] = None
    pfp: Optional[File] = None
    banner: Optional[File] = None
    stars: int = 0
    starred_by: List[PydanticObjectId] = []
    created_at: int = Field(default_factory=lambda: int(time()))
    modified_at: int = Field(default_factory=lambda: int(time()))
    admin: bool = False
    bot: bool = False
    bot_owner: Optional[PydanticObjectId] = None

    def gql(self) -> User:
        return User(
            id=str(self.id),
            username=str(self.username),
            display_name=self.display_name,
            bio=self.bio,
            pfp=self.pfp,
            banner=self.banner,
            stars=self.stars,
            starred_by=self.starred_by,
            created_at=self.created_at,
            modified_at=self.modified_at,
            admin=self.admin,
            bot=self.bot,
        )
