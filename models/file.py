import os

import strawberry
from pydantic import BaseModel
from opendal import AsyncOperator

CDN_PREFIX = os.getenv("CDN")

@strawberry.type
class File(BaseModel):
    loc: str

    # @strawberry.field
    # def absolute_path(self) -> str:
    #     return CDN_PREFIX + self.loc

    async def save(self, operator: AsyncOperator, bs: bytes):
        await operator.write(self.loc, bs)
