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

router = APIRouter(
    prefix='/user'
)


@router.get(
    path="/profile-photo"
)
async def get_profile_photo(
        user: dto.user = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    ...


@router.post("/token")
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        dao: HolderDao = Depends(dao_provider),
        settings: Settings = Depends(get_settings)
):
    http_status_401 = HTTPException(
        status_code=401,
        detail='incorrect phone_number or password'
    )
    auth = AuthProvider(settings=settings)
    user = await auth.authenticate_user(form_data, dao)
    if not user:
        raise http_status_401
    token = auth.create_user_token(user)
    return token


@router.post('/upload')
async def upload_file(file: UploadFile,
                      dao: HolderDao = Depends(dao_provider),
                      user: dto.user = Depends(get_current_user),
                      ):
    media_path = os.path.join(BASE_DIR / 'media/avatars')
    print(media_path)
    filename = file.filename
    filepath = f'{media_path}\\{filename}'

    db_photo_path = f'media/avatars/{filename}'

    async with aiofiles.open(f'{filepath}', 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    profile = await dao.profile.edit_photo(user_id=user.id, photo_path=db_photo_path)
    return {'filename': file.filename, 'saved': filepath, 'profile': profile}


@router.post(
    path='/login',
    description='Login user',
)
async def login(
        login_data: dto.UserLogin,
        dao: HolderDao = Depends(dao_provider),
        settings: Settings = Depends(get_settings)
):
    http_status_401 = HTTPException(
        status_code=401,
        detail='incorrect phone_number or password'
    )
    auth = AuthProvider(settings=settings)
    user = await auth.authenticate_user(login_data, dao)
    if not user:
        raise http_status_401
    token = auth.create_user_token(user)
    return token


@router.post(
    path="/tg-login",
    description="Login user via telegram passcode"
)
async def tg_login(
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
        user_profile = await dao.user.get_profile_by_user_id(user.id)
        user_out = UserOut(phone_number=user.phone_number, first_name=user_profile.first_name,
                           last_name=user_profile.last_name, username=user_profile.username,
                           is_active=user.is_active, is_staff=user.is_staff, is_superuser=user.is_superuser)
        return {'token': token, 'user': user_out}
    return http_status_401


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
            # print(f'no profile for {new_user}\ncreating profile')
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
    # for user in users:
    #     print(user.roles)
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


@router.get(
    path='/roles',
    description='Get all roles')
async def get_roles(
        # user: dto.user = Depends(get_user),
        dao: HolderDao = Depends(dao_provider)
) -> list[dto.RoleOut]:
    roles = await dao.role.get_roles()
    return roles


@router.post(
    path='/roles',
    description='Create role',
    status_code=201
)
async def create_role(
        role_data: dto.RoleCreate,
        user: dto.user = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    existing_role = await dao.role.get_role_by_name(role_data.name)
    if existing_role:
        raise HTTPException(
            status_code=400,
            detail=f'role with name {role_data.name} already exists'
        )
    role = await dao.role.add_role(role_data)
    return role


@router.patch(
    path='/roles/edit/{role_id}',
    description='Edit role'
)
async def edit_role(
        role_id: int,
        role_data: dto.RoleEdit,
        user: dto.user = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    role = await dao.role.edit_role(role_data, role_id)
    return role


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
