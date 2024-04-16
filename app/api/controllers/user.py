from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import dao_provider, get_settings, AuthProvider
from app.infrastructure.database.dao.holder import HolderDao
from app import dto
from app.config import Settings

router = APIRouter(
    prefix='/user'
)


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
        return new_user
    except ValueError as err:
        raise HTTPException(
            status_code=400,
            detail=str(err)
        )
