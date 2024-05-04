from typing import Union
import re
from pydantic import field_validator, Field, EmailStr, BaseModel
from datetime import datetime

from .base import serialize_time


class RoleBase(BaseModel):
    name: str
    # description: Union[str, None] = None

    class Config:
        json_encoders = {
            datetime: serialize_time
        }
        from_attributes = True
        orm_mode = True
        populate_by_name = True


class RoleOut(RoleBase):
    id: int


class RoleForUser(RoleBase):
    name: str


class RoleEdit(RoleBase):
    pass


class RoleCreate(RoleBase):
    pass


class Role(BaseModel):
    name: str
    description: Union[str, None] = None
