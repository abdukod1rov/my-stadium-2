from typing import Union, List, Optional
import re
from pydantic import field_validator, Field, EmailStr, BaseModel
from .role import Role, RoleOut, RoleForUser
from datetime import datetime

from ..infrastructure.database.models.user import UserRole


class UserBase(BaseModel):
    username : str
    phone_number: Union[str] = None


class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.CLIENT


class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


def serialize_time(value: datetime) -> str:
    return value.strftime('%d.%m.%Y %H:%M')


def validate_phone_number(phone_number: str) -> str:
    """
    Validate the format of a phone number.
    Raises a ValueError if the phone number is invalid.
    """
    pattern = r'^8\d{9}$'
    if not re.match(pattern, phone_number):
        raise ValueError('Invalid phone number')
    return phone_number


class User(BaseModel):
    phone_number: str = Field(
        description='User telefon raqami. Unique bo\'lish kerak',
        pattern=r'^8\d{9}',
        examples=['8908211633', ]
    )
    is_active: bool = True

    # _validate_phone_number = field_validator(validate_phone_number)

    class Config:
        json_encoders = {
            datetime: serialize_time
        }
        from_attributes = True
        orm_mode = True
        populate_by_name = True


class UserOut(User):
    username: Union[str, None] = None
    first_name: Union[str, None] = None
    last_name: Union[str, None] = None
    is_staff: bool
    is_superuser: bool
    roles: Union[List[RoleForUser], None] = None


class UserWithPassword(User):
    id: int
    password: str


class UserInCreate(User):
    password: str




class UserWithRoles(User):
    roles: List[Role]


class TgLogin(BaseModel):
    passcode: str


