from datetime import datetime,date
from decimal import Decimal
from typing import Union, Optional, List

from pydantic import BaseModel

from app.infrastructure.database.models.booking import AvailabilityStatus
from app.infrastructure.database.models.stadium import StadiumSize, SurfaceType


class WeeklyAvailability(BaseModel):
    date: date
    weekday: str
    status: AvailabilityStatus
    booking_count: int
    available_slots: int

class StadiumAvailabilityResponse(BaseModel):
    stadium_id: int
    stadium_name: str
    weekly_availability: List[WeeklyAvailability]

class StadiumBase(BaseModel):
    name: str
    description: Optional[str] = None
    address: str
    district: str
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    price_per_hour: Decimal
    size: StadiumSize
    surface: SurfaceType
    height: Decimal  # Stadium height in meters
    width: Decimal  # Stadium width in meters
    amenities: Optional[str] = None
    opening_hour: str = "06:00"
    closing_hour: str = "23:00"


class StadiumCreate(StadiumBase):
    pass


class StadiumUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    price_per_hour: Optional[Decimal] = None
    capacity: Optional[int] = None
    height: Optional[Decimal] = None
    width: Optional[Decimal] = None
    opening_hour: Optional[str] = None
    closing_hour: Optional[str] = None
    is_active: Optional[bool] = None


class StadiumResponse(StadiumBase):
    id: int
    owner_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True