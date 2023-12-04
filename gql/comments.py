from typing import List, Optional

from beanie.odm.fields import PydanticObjectId
from slugify import slugify
from strawberry.types import Info

from auth import authenticated
from error import ForumCreationError, ForumCreationErrorType
from gql import ForumSort, Page
from models.forum import DBForum, Forum


@authenticated()
async def create_commment(
    info: Info,
    post_id: str,
    content: str,
    reply_to: Optional[str] = None,
):
    pass
