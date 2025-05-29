
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import dao_provider, get_settings, AuthProvider
from app.api.dependencies.redis_passcode_manager import RedisPasscodeManager
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
    prefix='/api/v0/auth'
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
    auth = AuthProvider(settings=settings)
    passcode_manager = RedisPasscodeManager(redis_conn)

    http_status_401 = HTTPException(
        status_code=401,
        detail='Invalid or expired passcode'
    )

    # Get user ID by passcode
    user_id = await passcode_manager.get_user_id_by_passcode(login_data.passcode)
    if not user_id:
        raise http_status_401

    # Get user from database
    user = await dao.user.get_user_by_tg_id(user_id)
    if not user:
        raise http_status_401

    # Create token
    token = auth.create_user_token(user)
    user_out = UserResponse(
        phone_number=user.phone_number,
        role=user.role,
        created_at=user.created_at,
        is_active=user.is_active,
        username=user.username,
        id=user.id
    )

    # Clean up passcode after successful login (optional)
    await passcode_manager.cleanup_user_passcode(user_id)

    return {'token': token, 'user': user_out}