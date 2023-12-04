from typing import Optional

from strawberry.types import Info

from auth import authenticated


@authenticated()
async def create_commment(
    info: Info,
    post_id: str,
    content: str,
    reply_to: Optional[str] = None,
):
    pass
