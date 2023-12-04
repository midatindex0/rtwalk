from typing import List

from beanie.odm.fields import PydanticObjectId
from consts import MAX_FILE_SIZE
from strawberry.file_uploads import Upload
from strawberry.types import Info

from auth import authenticated
from error import FileUploadError, FileUploadErrorType
from models.file import File


@authenticated()
async def upload_files(files: List[Upload], info: Info) -> List[File]:
    user = await info.context.user()
    res = []
    for file in files:
        if file.size > MAX_FILE_SIZE:
            raise FileUploadError(
                "Maximum file size is 32mb", tp=FileUploadErrorType.FILE_TOO_BIG
            )
        content = await file.read()
        f = File(loc=f"{user.username}/{PydanticObjectId()}-{file.filename}")
        await f.save(info.context.op, content)
        res.append(f)
    return res
