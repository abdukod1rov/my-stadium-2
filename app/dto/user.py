from typing import Union, List
import re
from pydantic import field_validator, Field, EmailStr, BaseModel
from .role import Role, RoleOut, RoleForUser
from datetime import datetime


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

    _validate_phone_number = field_validator(__field='phone_number')(validate_phone_number)

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


class UserLogin(BaseModel):
    username: str = Field(
        field_name='phone_number',
        description='User telefon raqami. Unique bo\'lish kerak',
        pattern=r'^8\d{9}',
        examples=['8908211633', ]
    )
    password: str

    _validate_phone_number = field_validator(__field='username')(validate_phone_number)


class UserWithRoles(User):
    roles: List[Role]


class TgLogin(BaseModel):
    passcode: int


