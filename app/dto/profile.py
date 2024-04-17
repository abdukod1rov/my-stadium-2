from typing import Union
import re
from pydantic import field_validator, Field, EmailStr, BaseModel
from app import dto
from . import base
from datetime import datetime

from .base import serialize_time


class ProfileBase(BaseModel):
    username: Union[str, None] = None
    first_name: Union[str, None] = None
    last_name: Union[str, None] = None
    bio: Union[str, None] = None
    photo: Union[str, None] = None

    class Config:
        json_encoders = {
            datetime: serialize_time
        }
        from_attributes = True
        orm_mode = True
        populate_by_name = True


class ProfileCreate(BaseModel):
    user_id: int




class ProfileOut(ProfileBase):
    id: int
    user_id: int
