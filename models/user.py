from typing import Optional
from time import time
import os

import strawberry
from beanie import Document, Indexed
from pydantic import BaseModel, Field
from opendal import AsyncOperator

from models.file import File

class DBUser(Document):
    username: Indexed(str, unique=True)
    email: Indexed(str, unique=True)
    password: str
    display_name: str
    bio: Optional[File] = None
    pfp: Optional[File] = None
    banner: Optional[str] = None
    created_at: int = Field(default_factory=lambda: int(time()))
    modified_at: int = Field(default_factory=lambda: int(time()))
    admin: bool = False
    bot: bool = False


@strawberry.type
class User:
    username: str
    email: strawberry.Private[str]
    password: strawberry.Private[str]
    display_name: str
    bio: Optional[File] = None
    pfp: Optional[File] = None
    banner: Optional[str] = None
    created_at: int = Field(default_factory=lambda: int(time()))
    modified_at: int = Field(default_factory=lambda: int(time()))
    admin: bool = False
    bot: bool = False
