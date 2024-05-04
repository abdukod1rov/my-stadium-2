"""
Docstring:
Author: <Samandar Abdukodirov>
Email: <abdukodirovsamandar3@gmail.com>
Date: <2024>
License: <MIT>

Main router for stadium controller

"""
import os
from typing import List

import aiofiles
# TODO 1. Get All Stadiums with limit and offset
# TODO 2. Edit Stadium
# TODO 3. Add photo of the stadium


from fastapi import APIRouter, Depends, HTTPException, UploadFile
from starlette.responses import HTMLResponse

from app import dto
from app.api.dependencies import get_current_user, dao_provider
from app.api.dependencies.settings import BASE_DIR
from app.dto import User
import app.dto
from app.dto.stadium import StadiumOut, UpdateStadium
from app.infrastructure.database.dao.holder import HolderDao

router = APIRouter(
    prefix="/stadium",
    tags=["stadium"],

)


@router.post("/image")
async def create_upload_files(files: list[UploadFile]):
    return {"filenames": [file.filename for file in files]}


@router.get("/html")
async def main():
    content = """
<body>
<form action="/stadium/image" enctype="multipart/form-data" method="post">
<input name="files" type="file" multiple>
<input type="submit">
</form>
<form action="/image" enctype="multipart/form-data" method="post">
<input name="files" type="file" multiple>
<input type="submit">
</form>
</body>
    """
    return HTMLResponse(content=content)


@router.post(
    path="/image/{stadium_id}"
)
async def add_photo(
        files: List[UploadFile],
        stadium_id: int,
        dao: HolderDao = Depends(dao_provider),
        user: User = Depends(get_current_user)
):
    """
    Function to add a photo to the stadium
    """
    stadium = await dao.stadium.get_by_id(stadium_id)
    if not stadium:
        raise HTTPException(
            status_code=404,
            detail=f"Stadium {stadium_id} not found"
        )

    stadium_name = str(stadium.name)
    media_path = os.path.join(BASE_DIR / 'media/stadiums')
    if not os.path.exists(media_path):
        os.makedirs(media_path)

    stadium_path = f'{media_path}\\{stadium_name}'
    if not os.path.exists(stadium_path):
        os.makedirs(stadium_path)

    filepaths = []
    for file in files:
        filename = file.filename
        filepath = f'{media_path}\\{stadium_name}\\{filename}'
        filepaths.append(filepath)
        # Save the image path for the given stadium
        db_image_path = f"{media_path}/{filename}"

        async with aiofiles.open(f'{filepath}', 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
    return {"filenames": [file.filename for file in files],
            "filepaths": [filepath for filepath in filepaths]}


@router.get(
    path="/all",
    description="List all stadiums"
)
async def stadium_list(
        skip: int = 0,
        limit: int = 10,
        current_user: User = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    stadiums = await dao.stadium._get_all(skip=skip, limit=limit)
    return stadiums


@router.post(
    path="",
    description="Create a new stadium"
)
async def stadium_create(
        data: dto.StadiumCreate,
        user: dto.user = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider),
):
    stadium = await dao.stadium.create(owner_id=user.id, stadium_data=data)
    return stadium


@router.patch(
    path="/edit/{stadium_id}",
    description="Update a stadium"
)
async def stadium_edit(
        stadium_id: int,
        data: UpdateStadium,
        user: dto.user = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    get_stadium = await dao.stadium.get_by_id(stadium_id)
    if not get_stadium:
        raise HTTPException(
            status_code=400,
            detail=f"stadium {stadium_id} does not exist",
        )
    return await dao.stadium.update(stadium_id, data)
