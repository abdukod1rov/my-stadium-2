from datetime import datetime
from decimal import Decimal
from typing import Union

from pydantic import BaseModel, validator

from app.infrastructure.database.models.booking import BookingStatus


class BookingBase(BaseModel):
    stadium_id: int
    start_time: datetime
    end_time: datetime
    notes: Union[str] = None


class BookingCreate(BookingBase):
    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v


class BookingUpdate(BaseModel):
    start_time: Union[datetime] = None
    end_time: Union[datetime] = None
    notes: Union[str] = None
    status: Union[BookingStatus] = None


class BookingResponse(BookingBase):
    id: int
    user_id: int
    total_price: Decimal
    status: BookingStatus
    created_at: datetime

    class Config:
        from_attributes = True