from typing import List, Optional

from beanie.odm.fields import PydanticObjectId
from slugify import slugify
from strawberry.types import Info

from auth import authenticated
from error import ForumCreationError, ForumCreationErrorType
from gql import ForumSort, Page
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


async def get_forum(
    id: Optional[str] = None, name: Optional[str] = None
) -> Optional[Forum]:
    if id:
        forum = await DBForum.find_one(DBForum.id == PydanticObjectId(id))
        return forum.gql() if forum else None
    if name:
        forum = await DBForum.find_one(DBForum.name == name)
        return forum.gql() if forum else None


async def get_forums(
    info: Info,
    ids: Optional[List[str]] = None,
    owner_id: Optional[str] = None,
    names: Optional[List[str]] = None,
    search: Optional[str] = None,
    locked: Optional[bool] = None,
    created_after: Optional[int] = None,
    created_before: Optional[int] = None,
    sort: Optional[ForumSort] = None,
    page: int = 1,
    limit: int = 10,
) -> Page[Forum]:
    if ids:
        ids = [*map(PydanticObjectId, ids)]
        forums = DBForum.find(In(DBForum.id, ids))
    elif names:
        forums = DBForum.find(In(DBForum.name, names))
    elif owner_id:
        forums = DBForum.find(DBForum.owner_id == PydanticObjectId(owner_id))
    else:
        forums = DBForum.find_all()
    if search:
        forums = forums.aggregate(
            [
                {
                    "$search": {
                        "index": "forums",
                        "text": {
                            "query": search,
                            "path": ["name", "display_name", "description"],
                            "fuzzy": {},
                        },
                    }
                }
            ],
            projection_model=DBForum,
        )
    if isinstance(locked, bool):
        forums.find(DBForum.locked == locked)
    if created_after:
        forums.find(DBForum.created_at > created_after)
    if created_before:
        forums.find(DBForum.created_at < created_before)
    if sort:
        if sort == ForumSort.CREATED_AT_ASC:
            forums.sort(+DBForum.created_at)
        elif sort == ForumSort.CREATED_AT_DESC:
            forums.sort(-DBForum.created_at)
    total = 0
    for selection in info.selected_fields:
        if selection.name == "getForums":
            for field in selection.selections:
                if field.name == "total":
                    total = await forums.count()
                    break

    limit = min(20, limit)
    forums.skip(limit * (page - 1)).limit(limit)
    forums = await forums.to_list()

    return Page(
        total=total,
        next_page=page + 1 if len(forums) == limit else None,
        items=[*map(DBForum.gql, forums)],
    )
