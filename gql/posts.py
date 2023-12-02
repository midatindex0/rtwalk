from typing import List, Optional

from beanie.odm.fields import PydanticObjectId
from strawberry.types import Info

from auth import authenticated
from error import PostCreationError, PostCreationErrorType
from models.forum import DBForum
from models.post import DBPost, Post


@authenticated()
async def create_post(
    info: Info,
    forum_id: str,
    title: str,
    tags: Optional[List[str]] = None,
    content: Optional[str] = None,
    attachments: Optional[List[str]] = None,
) -> Post:
    user = await info.context.user()
    forum: DBForum = await DBForum.find_one(DBForum.id == PydanticObjectId(forum_id))
    if not forum:
        raise PostCreationError(
            "Forum not found", tp=PostCreationErrorType.FORUM_NOT_FOUND
        ).into()
    if forum.locked and not user.admin:
        raise PostCreationError(
            "Forum is locked", tp=PostCreationErrorType.LOCKED_FORUM
        ).into()
    forum.post_count += 1
    await forum.save()
    return (
        await DBPost(
            title=title,
            tags=tags,
            content=content,
            attachments=[*map(lambda a: File(loc=a), attachments)]
            if attachments
            else None,
            poster_id=user.id,
            forum_id=forum.id,
        ).insert()
    ).gql()
