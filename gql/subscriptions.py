import ast

from broadcaster import Broadcast
from fastapi import APIRouter, WebSocket

router = APIRouter()


@router.websocket("/")
async def rte_websocket(
    ws: WebSocket,
    comment_new: bool = False,
    comment_edit: bool = False,
    post_new: bool = False,
    post_edit: bool = False,
):
    broadcast: Broadcast = ws.state.broadcast
    await ws.accept()
    async with broadcast.subscribe(channel="rte") as subscriber:
        async for event in subscriber:
            msg = ast.literal_eval(event.message)
            if msg["event"] == "COMMENT_NEW" and comment_new:
                await ws.send_json(msg)
            elif msg["event"] == "COMMENT_EDIT" and not comment_edit:
                continue
            elif msg["event"] == "POST_NEW" and not post_new:
                continue
            elif msg["event"] == "POST_EDIT" and not post_edit:
                continue
