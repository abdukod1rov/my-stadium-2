from typing import Union
import re
from pydantic import field_validator, Field, EmailStr, BaseModel
from app import dto
from . import base
from datetime import datetime

from .base import serialize_time


class RoleBase(BaseModel):
    name: str
    description: Union[str, None] = None

    class Config:
        json_encoders = {
            datetime: serialize_time
        }
        from_attributes = True
        orm_mode = True
        populate_by_name = True


class RoleOut(RoleBase):
    id: int


class RoleEdit(RoleBase):
    pass


class RoleCreate(RoleBase):
    pass
