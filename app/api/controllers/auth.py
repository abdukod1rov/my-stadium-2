from typing import Annotated

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import dao_provider, get_settings, AuthProvider, get_current_user
from app.dto import UserOut, UserResponse
from app.infrastructure.database.dao.holder import HolderDao
from app import dto
from app.config import Settings

import os
from app.api.dependencies.settings import BASE_DIR, get_redis_connection
from redis import asyncio as redis_asyncio

# TODO 1. Save user profile image in the local directory

# FOR ACTIONS RUNNER
router = APIRouter(
    prefix='/auth'
)


@router.post(
    path="/login",
    description="Login user via telegram passcode"
)
async def login(
        login_data: dto.TgLogin,
        redis_conn: redis_asyncio.Redis = Depends(get_redis_connection),
        dao: HolderDao = Depends(dao_provider),
        settings: Settings = Depends(get_settings),
):
    """
    @return:
    phone_number,
    first_name|last_name|username
    """
    auth = AuthProvider(settings=settings)
    http_status_401 = HTTPException(
        status_code=401,
        detail='invalid passcode'
    )
    # Perform a lookup to get the user ID associated with the passcode
    stored_user_id = await redis_conn.get(str(login_data.passcode))
    if not stored_user_id:
        raise http_status_401

    user = await dao.user.get_user_by_tg_id(int(stored_user_id))
    if user is not None:
        token = auth.create_user_token(user)
        user_out = UserResponse(first_name=user.first_name, last_name=user.last_name, phone_number=user.phone_number,
                                role=user.role, created_at=user.created_at, is_active=user.is_active, username=user.username,
                                id=user.id)
        return {'token': token, 'user': user_out}

    return http_status_401