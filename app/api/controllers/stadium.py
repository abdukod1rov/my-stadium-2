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
# TODO 4. Create facilities and get facilities
# TODO 5. Get All stadiums with price and rating


from fastapi import APIRouter, Depends, HTTPException, UploadFile
from starlette.responses import HTMLResponse

from app import dto
from app.api.dependencies import get_current_user, dao_provider
from app.api.dependencies.settings import BASE_DIR
from app.dto import User
import app.dto
from app.dto.stadium import StadiumOut, UpdateStadium, StadiumWithPriceAndRating
from app.dto.stadium2 import StadiumUpdate, StadiumCreate
from app.dto.user import UserResponse
from app.infrastructure.database.dao.holder import HolderDao
from app.infrastructure.database.models.user import UserRole
# Stadium Routes
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional


stadium_router = APIRouter(prefix="/stadiums")


@stadium_router.get("/", description="List all stadiums")
async def stadium_list(
        skip: int = 0,
        limit: int = 10,
        city: Optional[str] = Query(None),
        surface: Optional[str] = Query(None),
        size: Optional[str] = Query(None),
        dao: HolderDao = Depends(dao_provider)
):
    if city or surface or size:
        stadiums = await dao.stadium.search(city=city, surface=surface, size=size, skip=skip, limit=limit)
    else:
        stadiums = await dao.stadium._get_all(skip=skip, limit=limit)
    return stadiums


@stadium_router.get("/{stadium_id}", description="Get stadium by ID")
async def stadium_detail(
        stadium_id: int,
        dao: HolderDao = Depends(dao_provider)
):
    stadium = await dao.stadium._get_by_id(stadium_id)
    if not stadium:
        raise HTTPException(status_code=404, detail="Stadium not found")
    return stadium


@stadium_router.post("/", description="Create new stadium")
async def stadium_create(
        data: StadiumCreate,
        user: UserResponse = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    if user.role not in [UserRole.STADIUM_OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    stadium = await dao.stadium.create(stadium_data=data, owner_id=user.id)
    return stadium


@stadium_router.put("/{stadium_id}", description="Update stadium")
async def stadium_update(
        stadium_id: int,
        data: StadiumUpdate,
        user: UserResponse = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    stadium = await dao.stadium.update(stadium_id=stadium_id, stadium_data=data, owner_id=user.id)
    return stadium


@stadium_router.delete("/{stadium_id}", description="Delete stadium")
async def stadium_delete(
        stadium_id: int,
        user: UserResponse = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    # Check ownership
    stadium = await dao.stadium._get_by_id(stadium_id)
    if not stadium or (stadium.owner_id != user.id and user.role != UserRole.ADMIN):
        raise HTTPException(status_code=404, detail="Stadium not found or access denied")

    success = await dao.stadium._delete(stadium_id)
    if not success:
        raise HTTPException(status_code=404, detail="Stadium not found")
    return {"message": "Stadium deleted successfully"}


@stadium_router.get("/{stadium_id}/availability", description="Get stadium weekly availability")
async def stadium_weekly_availability(
        stadium_id: int,
        dao: HolderDao = Depends(dao_provider)
):
    availability = await dao.stadium.get_weekly_availability(stadium_id)
    return availability










@stadium_router.post("/image")
async def create_upload_files(files: list[UploadFile]):
    return {"filenames": [file.filename for file in files]}



@stadium_router.post(
    path="/image/{stadium_id}"
)
async def add_photo(
        file: UploadFile,
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

    stadium_name = str(stadium.name).replace(" ", "_").lower()
    media_path = os.path.join(BASE_DIR / 'media/stadiums')
    print(media_path)
    if not os.path.exists(media_path):
        os.makedirs(media_path)
    stadium_path = f'{media_path}\\{stadium_name}'
    if not os.path.exists(stadium_path):
        os.makedirs(stadium_path)

    filename = file.filename
    filepath = f'{media_path}\\{stadium_name}\\{filename}'
    # Save the image path for the given stadium
    db_image_path = str(f"media//stadiums//{stadium_name}//{filename}")
    async with aiofiles.open(f'{filepath}', 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
        update_stadium = dto.UpdateStadium(image=db_image_path)
        await dao.stadium.update(stadium_id, update_stadium)
    return stadium



