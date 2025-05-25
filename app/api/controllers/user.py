"""_User endpoints_
    Completed routers
    1./register
    2./login
    3./get-user {phone_number}
    4./get-profile
    5./edit-profile
    6./me
    7./upload-photo
    8./create-role
    9./get-roles
    10./edit-role
    11./assign-role

    
    <-- Waiting to be completed -->
    1. /delete-user
    2./delete-profile
    3./delete-role
    4./delete-roles
    
    
    Raises:
        http_status_401: _description_
        HTTPException: _description_
        HTTPException: _description_
        HTTPException: _description_

    Returns:
        _type_: _description_
"""
from typing import Annotated

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials, OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import dao_provider, get_settings, AuthProvider, get_current_user
from app.dto import UserOut
from app.infrastructure.database.dao.holder import HolderDao
from app import dto
from app.config import Settings

import os
from app.api.dependencies.settings import BASE_DIR, get_redis_connection
from redis import asyncio as redis_asyncio

# TODO 1. Save user profile image in the local directory

# FOR ACTIONS RUNNER
router = APIRouter(
    prefix='/user'
)

@router.post(
    path='/register',
    description='Register user',
    status_code=201,
)
async def create_user(
        user_data: dto.UserInCreate,
        settings: Settings = Depends(get_settings),
        dao: HolderDao = Depends(dao_provider),
):
    auth = AuthProvider(settings)
    user = await dao.user.get_user(user_data.phone_number)
    if user is not None:
        raise HTTPException(
            status_code=400,
            detail=f'user with {user_data.phone_number} already registered'
        )
    try:
        hashed_password = auth.get_password_hash(user_data.password)
        user_data.password = hashed_password
        new_user = await dao.user.add_user(user_data=user_data)
        profile = await dao.profile.get_by_id(new_user.id)

        if profile is None:
            user_profile = await dao.profile.create_profile(user_id=new_user.id)
        return new_user

    except ValueError as err:
        raise HTTPException(
            status_code=400,
            detail=str(err)
        )


@router.get(path='/me', description='Get current user')
async def get_me(
        user: dto.user = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    user = await dao.user.get_user_by_id(user.id)
    print(user.id)
    return user


@router.get(
    path='/all',
    description='Get all users')
async def get_users(
        dao: HolderDao = Depends(dao_provider)
):
    users = await dao.user.get_users()
    return users


@router.delete(
    path="/delete",
    description="Delete user"
)
async def delete_user(
        dao: HolderDao = Depends(dao_provider),
        user: dto.user = Depends(get_current_user)
):
    user_from_db = await dao.user.get_by_id(user.id)
    await dao.user.delete(user_from_db)
    return 'OK'


@router.patch(
    path='/profile/edit',
    description='Edit profile'
)
async def edit_profile(
        profile_data: dto.ProfileBase,
        user: dto.user = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider),
):
    profile = await dao.profile.edit_profile(user.id, profile_data)
    return profile


@router.get(
    path='/profile',
    description='Get user profile',
    response_model=dto.ProfileOut)
async def get_profile(
        user: dto.user = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)):
    profile = await dao.profile.get_profile_by_user(user.id) or await dao.profile.create_profile(user.id)
    print(profile.user.phone_number)
    print(profile.user.is_active)
    return profile


from pydantic import BaseModel


class Role(BaseModel):
    role_name: str


@router.post(
    path="/{user_id}/assign-role",
    description="Assign role to the user"
)
async def assign_role(
        user_id: int,
        role: Role,
        # user: dto.User = Depends(get_user),
        dao: HolderDao = Depends(dao_provider)
):
    return await dao.user.assign_role(user_id, role.role_name)
