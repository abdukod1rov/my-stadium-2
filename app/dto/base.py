import datetime
from typing import Union

from pydantic import BaseModel, Field


def serialize_time(value: datetime) -> str:
    return value.strftime('%d.%m.%Y %H:%M')


class Base(BaseModel):
    created_at: datetime.datetime = Field(alias='createdAt')
    updated_at: Union[datetime.datetime, None] = Field(alias='updatedAt')

    class Config:
        json_encoders = {
            datetime: serialize_time
        }
        from_attributes = True
        orm_mode = True
        populate_by_name = True


