from typing import List, Optional

from beanie.odm.fields import PydanticObjectId
from strawberry.types import Info

from auth import authenticated
from error import PostCreationError, PostCreationErrorType
from gql import Page, PostSort
from models.forum import DBForum
from models.post import DBPoll, DBPost, Post


@authenticated()
async def create_post(
    info: Info,
    forum_id: str,
    title: str,
    tags: Optional[List[str]] = None,
    content: Optional[str] = None,
    attachments: Optional[List[str]] = None,
    poll: Optional[List[str]] = None,
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
    if user.id in forum.banned_members:
        raise PostCreationError(
            "You are banned in this forum", tp=PostCreationErrorType.BANNED_MEMBER
        ).into()
    if poll and len(poll) < 2:
        raise PostCreationError(
            "Poll should atlest have 2 options", tp=PostCreationErrorType.INVALID_POLL
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
            poll=DBPoll(
                options=poll, results=[0] * len(poll), participants=[[]] * len(poll)
            )
            if poll
            else None,
            poster_id=user.id,
            forum_id=forum.id,
        ).insert()
    ).gql()


async def get_post(id: str) -> Optional[Post]:
    post = await DBPost.find_one(DBPost.id == PydanticObjectId(id))
    return post.gql() if post else None


async def get_posts(
    info: Info,
    ids: Optional[List[str]] = None,
    poster_id: Optional[str] = None,
    forum_id: Optional[str] = None,
    search: Optional[str] = None,
    created_after: Optional[int] = None,
    created_before: Optional[int] = None,
    sort: Optional[PostSort] = None,
    page: int = 1,
    limit: int = 10,
) -> Page[Post]:
    aggregation_pipe = []
    if ids:
        ids = [*map(PydanticObjectId, ids)]
        posts = DBPost.find(In(DBPost.id, ids))
    elif poster_id:
        posts = DBPost.find(DBPost.poster_id == PydanticObjectId(poster_id))
    elif forum_id:
        posts = DBPost.find(DBPost.forum_id == PydanticObjectId(forum_id))
    else:
        posts = DBPost.find_all()
    if search:
        aggregation_pipe.append(
            {
                "$search": {
                    "index": "posts",
                    "text": {
                        "query": search,
                        "path": ["title", "tags", "content", "poll.options"],
                        "fuzzy": {},
                    },
                }
            }
        )
    if created_after:
        aggregation_pipe.append({"$match": {"created_at": {"$gt": created_after}}})
    if created_before:
        aggregation_pipe.append({"$match": {"created_at": {"$lt": created_before}}})
    if sort:
        if sort == PostSort.CREATED_AT_ASC:
            aggregation_pipe.append({"$sort": {"created_at": 1}})
        elif sort == PostSort.CREATED_AT_DESC:
            aggregation_pipe.append({"$sort": {"created_at": -1}})
        elif sort == PostSort.PINNED:
            aggregation_pipe.append({"$sort": {"pinned": 1}})
        elif sort == PostSort.UPVOTES:
            aggregation_pipe.append({"$sort": {"upvotes": 1}})
        elif sort == PostSort.DOWNVOTES:
            aggregation_pipe.append({"$sort": {"downvotes": 1}})
    total = 0
    for selection in info.selected_fields:
        if selection.name == "getPosts":
            for field in selection.selections:
                if field.name == "total":
                    p = aggregation_pipe.copy()
                    p.append({"$count": "total"})
                    try:
                        total = (
                            await posts.aggregate(aggregation_pipeline=p).to_list()
                        )[0]["total"]
                    except:
                        pass
                    break

    page = max(1, page)
    limit = max(min(20, limit), 1)
    aggregation_pipe.append({"$skip": limit * (page - 1)})
    aggregation_pipe.append({"$limit": limit})
    posts = posts.aggregate(aggregation_pipe, projection_model=DBPost)
    posts = await posts.to_list()

    return Page(
        total=total,
        next_page=page + 1 if len(posts) == limit else None,
        items=[*map(DBPost.gql, posts)],
    )
