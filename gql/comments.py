from typing import List, Optional

from beanie.odm.fields import PydanticObjectId
from beanie.operators import In
from strawberry.types import Info

from auth import authenticated
from error import CommentCreationError, CommentCreationErrorType
from gql import CommentSort, Page
from models.comment import Comment, DBComment
from models.forum import DBForum
from models.post import DBPost


@authenticated()
async def create_commment(
    info: Info,
    post_id: str,
    content: str,
    reply_to: Optional[str] = None,
) -> Comment:
    user = await info.context.user()
    post = await DBPost.find_one(DBPost.id == PydanticObjectId(post_id))
    if not post:
        raise CommentCreationError(
            "Post does not exist",
            tp=CommentCreationErrorType.POST_NOT_FOUND,
        )
    # TODO: Do this @ban check in query
    forum = await DBForum.find_one(DBForum.id == post.forum_id)
    if user.id in forum.banned_members:
        raise CommentCreationError(
            "You are banned in this forum",
            tp=CommentCreationErrorType.BANNED_MEMBER,
        )

    if reply_to:
        parent = await DBComment.find_one(DBComment.id == PydanticObjectId(reply_to))
        if not parent:
            raise CommentCreationError(
                "Parent comment does not exist",
                tp=CommentCreationErrorType.PARENT_NOT_FOUND,
            )
        parent.reply_count += 1
        await parent.save()
    comment = DBComment(
        content=content,
        commenter_id=user.id,
        reply_to=PydanticObjectId(reply_to) if reply_to else None,
        post_id=post.id,
    )
    post.comment_count += 1
    await post.save()
    await comment.insert()
    return comment


async def get_comment(id: str) -> Optional[Comment]:
    comment = await DBComment.find_one(DBComment.id == PydanticObjectId(id))
    return comment.gql() if comment else None


async def get_comments(
    info: Info,
    ids: Optional[List[str]] = None,
    commenter_id: Optional[str] = None,
    post_id: Optional[str] = None,
    reply_to: Optional[str] = None,
    parent: Optional[bool] = None,
    created_after: Optional[int] = None,
    created_before: Optional[int] = None,
    sort: Optional[CommentSort] = None,
    page: int = 1,
    limit: int = 10,
) -> Page[Comment]:
    aggregation_pipe = []
    if ids:
        ids = [*map(PydanticObjectId, ids)]
        comments = DBComment.find(In(DBComment.id, ids))
    elif commenter_id:
        comments = DBComment.find(
            DBComment.commenter_id == PydanticObjectId(commenter_id)
        )
    elif post_id:
        comments = DBComment.find(DBComment.post_id == PydanticObjectId(post_id))
    elif reply_to:
        comments = DBComment.find(DBComment.reply_to == PydanticObjectId(reply_to))
    else:
        comments = DBComment.find_all()
    # if search:
    #     aggregation_pipe.append(
    #         {
    #             "$search": {
    #                 "index": "comments",
    #                 "text": {
    #                     "query": search,
    #                     "path": ["title", "tags", "content", "poll.options"],
    #                     "fuzzy": {},
    #                 },
    #             }
    #         }
    #     )
    if isinstance(parent, bool):
        if parent:
            comments = DBComment.find(DBComment.reply_to == None)
        else:
            comments = DBComment.find(DBComment.reply_to != None)
    if created_after:
        aggregation_pipe.append({"$match": {"created_at": {"$gt": created_after}}})
    if created_before:
        aggregation_pipe.append({"$match": {"created_at": {"$lt": created_before}}})
    if sort:
        if sort == CommentSort.CREATED_AT_ASC:
            aggregation_pipe.append({"$sort": {"created_at": 1}})
        elif sort == CommentSort.CREATED_AT_DESC:
            aggregation_pipe.append({"$sort": {"created_at": -1}})
    total = 0
    for selection in info.selected_fields:
        if selection.name == "getComments":
            for field in selection.selections:
                if field.name == "total":
                    p = aggregation_pipe.copy()
                    p.append({"$count": "total"})
                    try:
                        total = (
                            await comments.aggregate(aggregation_pipeline=p).to_list()
                        )[0]["total"]
                    except:
                        pass
                    break

    page = max(1, page)
    limit = max(min(100, limit), 1)
    aggregation_pipe.append({"$skip": limit * (page - 1)})
    aggregation_pipe.append({"$limit": limit})
    comments = comments.aggregate(aggregation_pipe, projection_model=DBComment)
    comments = await comments.to_list()

    return Page(
        total=total,
        next_page=page + 1 if len(comments) == limit else None,
        items=[*map(DBComment.gql, comments)],
    )
