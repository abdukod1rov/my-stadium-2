from datetime import timedelta, datetime, timezone

from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from app import dto
from .settings import get_settings
from .database import dao_provider
from app.infrastructure.database.dao.holder import HolderDao
from app.config import Settings


from fastapi import Depends, HTTPException, status, Header
from typing import Optional

class PasscodeAuth:
    """Custom authentication scheme for passcode-based auth"""

    def __init__(self):
        pass

    async def __call__(self, authorization: Optional[str] = Header(None)) -> str:
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return token
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"},
            )


passcode_auth = PasscodeAuth()


class AuthProvider:
    def __init__(self, settings: Settings):
        self.settings = settings
        # Remove password context since we don't use passwords
        self.secret_key = settings.api.secret
        self.algorithm = 'HS256'
        self.access_token_expires = timedelta(days=3)

    def create_access_token(self, data: dict, expires_delta: timedelta) -> dto.Token:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta

        to_encode.update({'exp': expire})
        encoded_jwt = jwt.encode(
            claims=to_encode,
            key=self.secret_key,
            algorithm=self.algorithm
        )
        return dto.Token(
            access_token=encoded_jwt,
            token_type='bearer'
        )

    def create_user_token(self, user: dto.User) -> dto.Token:
        return self.create_access_token(
            data={
                'sub': str(user.id),  # Use user ID instead of phone
                'user_id': user.id,
                'role': user.role  # Include role in token
            },
            expires_delta=self.access_token_expires
        )



async def get_current_user(
        token: str = Depends(passcode_auth),
        dao: HolderDao = Depends(dao_provider)
) -> dto.UserOut:
    """Get current user from JWT token (no password verification needed)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token
        settings = get_settings()  # You might need to inject this
        auth = AuthProvider(settings)

        payload = jwt.decode(
            token=token,
            key=auth.secret_key,
            algorithms=[auth.algorithm]
        )

        user_id = payload.get('user_id')
        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Get user by ID instead of phone number
    user = await dao.user.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception

    return user


async def get_admin_user(
        current_user: dto.UserOut = Depends(get_current_user)
) -> dto.UserOut:
    """Dependency to ensure current user has admin privileges"""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    if hasattr(current_user, 'is_active') and not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive"
        )

    return current_user