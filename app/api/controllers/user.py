import aiofiles
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from app.api.dependencies import dao_provider, get_settings, AuthProvider, get_user
from app.infrastructure.database.dao.holder import HolderDao
from app import dto
from app.config import Settings

import os
from app.api.dependencies.settings import BASE_DIR

# TODO 1. Save user profile image in the local directory

router = APIRouter(
    prefix='/user'
)


@router.post('/upload')
async def upload_file(file: UploadFile,
                      dao: HolderDao = Depends(dao_provider),
                      user: dto.user = Depends(get_user),
                      ):
    user_obj = await user
    media_path = os.path.join(BASE_DIR / 'media/avatars')
    print(media_path)
    filename = file.filename
    filepath = f'{media_path}\\{filename}'

    db_photo_path = f'media/avatars/{filename}'

    async with aiofiles.open(f'{filepath}', 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    profile = await dao.profile.edit_photo(user_id=user_obj.id, photo_path=db_photo_path)
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
    path='/register',
    description='Register user',
    status_code=201
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
        profile = await dao.profile.get_profile(new_user.id)
        if not profile:
            print(f'no profile for {new_user.phone_number}\ncreating profile')
            user_profile = await dao.profile.create_profile(user_id=new_user.id)
        return new_user
    except ValueError as err:
        raise HTTPException(
            status_code=400,
            detail=str(err)
        )


@router.get(path='/me', description='Get current user')
async def get_current_user(
        user: dto.user = Depends(get_user)
):
    return await user


@router.get(
    path='/all',
    description='Get all users')
async def get_users(
        user: dto.user = Depends(get_user),
        dao: HolderDao = Depends(dao_provider)
)-> list[dto.UserOut]:
    users = await dao.user.get_users()
    return users


@router.patch(
    path='/profile/edit',
    description='Edit profile'
)
async def edit_profile(
        profile_data: dto.ProfileBase,
        user: dto.user = Depends(get_user),
        dao: HolderDao = Depends(dao_provider),
):
    user_object = await user
    profile = await dao.profile.edit_profile(user_object.id, profile_data)
    return profile


@router.get(
    path='/profile',
    description='Get user profile')
async def get_profile(
        user: dto.user = Depends(get_user),
        dao: HolderDao = Depends(dao_provider)):
    user_object = await user
    profile = await dao.profile.get_profile(user_object.id) or await dao.profile.create_profile(user_object.id)
    return profile


@router.get(
    path='/roles',
    description='Get all roles')
async def get_roles(
        user: dto.user = Depends(get_user),
        dao: HolderDao = Depends(dao_provider)
):
    roles = await dao.role.get_roles()
    return roles


@router.post(
    path='/roles',
    description='Create role',
    status_code=201
)
async def create_role(
        role_data: dto.RoleCreate,
        user: dto.user = Depends(get_user),
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
        user: dto.user = Depends(get_user),
        dao: HolderDao = Depends(dao_provider)
):
    role = await dao.role.edit_role(role_data, role_id)
    return role
