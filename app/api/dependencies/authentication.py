from datetime import timedelta, datetime, timezone
from typing import Union, Type

from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from starlette import status

from app import dto
from .database import dao_provider
from app.infrastructure.database.dao.holder import HolderDao
from app.config import Settings
from ...infrastructure.database.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/login')


def get_user(token: str = Depends(oauth2_scheme)) -> dto.User:
    ...


class AuthProvider:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
        self.secret_key = settings.api.secret
        self.algorithm = 'HS256'
        self.access_token_expires = timedelta(days=3)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, plain_password: str) -> str:
        return self.pwd_context.hash(plain_password)

    def create_access_token(self, data: dict, expires_delta: timedelta) -> dto.Token:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta

        to_encode.update({'exp': expire})
        encoded_jwt = jwt.encode(claims=to_encode,
                                 key=self.secret_key,
                                 algorithm=self.algorithm)
        return dto.Token(
            access_token=encoded_jwt,
            token_type='bearer'
        )

    def create_user_token(self, user: dto.User) -> dto.Token:
        return self.create_access_token(
            data={
                'sub': user.phone_number,
                'user_id': user.id
            },
            expires_delta=self.access_token_expires
        )

    async def authenticate_user(self,
                                login_data: dto.UserLogin,
                                dao: HolderDao) -> Union[dto.User, bool]:

        user = await dao.user.get_user_with_password(user_data=login_data)
        if not user:
            return False
        if not self.verify_password(login_data.password, user.password):
            return False

        return user

    async def get_current_user(self,
                               token: str = Depends(oauth2_scheme),
                               dao: HolderDao = Depends(dao_provider)
                               ) -> dto.User:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token=token, key=self.secret_key, algorithms=[self.algorithm])
            phone_number = payload.get('sub')
            if phone_number is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        user = dao.user.get_user(phone_number)
        if user is None:
            raise credentials_exception
        return user
