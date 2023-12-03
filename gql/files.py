from typing import List

from beanie.odm.fields import PydanticObjectId
from strawberry.file_uploads import Upload
from strawberry.types import Info

from auth import authenticated
from models.file import File


@authenticated()
async def upload_files(files: List[Upload], info: Info) -> List[File]:
    user = await info.context.user()
    res = []
    for file in files:
        content = await file.read()
        print(file.size)
        f = File(loc=f"{user.username}/{PydanticObjectId()}-{file.filename}")
        await f.save(info.context.op, content)
        res.append(f)
    return res
