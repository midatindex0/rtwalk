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
    aggregation_pipe = []
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
        aggregation_pipe.append(
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
        )
    if isinstance(locked, bool):
        aggregation_pipe.append({"$match": {"locked": locked}})
    if created_after:
        aggregation_pipe.append({"$match": {"created_at": {"$gt": created_after}}})
    if created_before:
        aggregation_pipe.append({"$match": {"created_at": {"$lt": created_before}}})
    if sort:
        if sort == ForumSort.CREATED_AT_ASC:
            aggregation_pipe.append({"$sort": {"created_at": 1}})
        elif sort == ForumSort.CREATED_AT_DESC:
            aggregation_pipe.append({"$sort": {"created_at": -1}})
    total = 0
    for selection in info.selected_fields:
        if selection.name == "getForums":
            for field in selection.selections:
                if field.name == "total":
                    p = aggregation_pipe.copy()
                    p.append({"$count": "total"})
                    try:
                        total = (
                            await forums.aggregate(aggregation_pipeline=p).to_list()
                        )[0]["total"]
                    except:
                        pass
                    break

    page = max(1, page)
    limit = max(min(20, limit), 1)
    aggregation_pipe.append({"$skip": limit * (page - 1)})
    aggregation_pipe.append({"$limit": limit})
    forums = forums.aggregate(aggregation_pipe, projection_model=DBForum)
    forums = await forums.to_list()

    return Page(
        total=total,
        next_page=page + 1 if len(forums) == limit else None,
        items=[*map(DBForum.gql, forums)],
    )
