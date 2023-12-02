from slugify import slugify
from strawberry.types import Info

from auth import authenticated
from error import ForumCreationErrorType, ForumCreationError
from gql import Ok, Page, UserSort, BotCreds
from models.forum import DBForum, Forum


@authenticated(bot=False)
async def create_forum(info: Info, name: str) -> Forum:
    user = await info.context.user()
    name = slugify(name)
    if len(name) < 2:
        raise ForumCreationError(
            "Forum name must be atlest 2 characters long",
            tp=ForumCreationErrorType.INVALID_NAME,
        )
    f = await DBForum.find_one(DBForum.name == name)
    if f:
        raise ForumCreationError(
            "Forum already exists",
            tp=ForumCreationErrorType.FORUM_ALREADY_EXISTS,
        )
    return (
        await DBForum(
            name=name,
            display_name=name,
            owner_id=user.id,
        ).insert()
    ).gql()
