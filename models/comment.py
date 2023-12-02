from time import time
from typing import List, Optional

from beanie import Document
from beanie.odm.fields import PydanticObjectId
from pydantic import Field


class DBComment(Document):
    content: Optional[str] = None
    commenter_id: PydanticObjectId
    parent_id: Optional[PydanticObjectId] = None
    post_id: PydanticObjectId
    created_at: int = Field(default_factory=lambda: int(time()))
    modified_at: int = Field(default_factory=lambda: int(time()))
    upvotes: int = 0
    downvotes: int = 0
    upvoted_by: List[PydanticObjectId] = Field(default=[])
    downvoted_by: List[PydanticObjectId] = [Field(default=[])]
