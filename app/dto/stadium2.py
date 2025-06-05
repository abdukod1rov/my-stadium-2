from datetime import datetime, date
from decimal import Decimal
from typing import Union, Optional, List

from pydantic import BaseModel

from app.infrastructure.database.models.booking import AvailabilityStatus
from app.infrastructure.database.models.stadium import StadiumSize, SurfaceType
from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Optional
from datetime import datetime
from fastapi import UploadFile, HTTPException
import mimetypes
from PIL import Image
import io


# Image DTOs
class ImageCreateDTO(BaseModel):
    url: str = Field(..., description="Image URL path")
    alt_text: Optional[str] = Field(None, max_length=255, description="Alt text for accessibility")
    stadium_id: int = Field(..., gt=0, description="Stadium ID")
    is_primary: bool = Field(False, description="Whether this is the primary image")


class ImageUpdateDTO(BaseModel):
    url: Optional[str] = Field(None, description="Image URL path")
    alt_text: Optional[str] = Field(None, max_length=255, description="Alt text for accessibility")
    is_primary: Optional[bool] = Field(None, description="Whether this is the primary image")


class ImageResponseDTO(BaseModel):
    id: int
    url: str
    alt_text: Optional[str]
    stadium_id: int
    is_primary: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StadiumImagesResponseDTO(BaseModel):
    stadium_id: int
    stadium_name: str
    total_images: int
    primary_image: Optional[str] = None
    images: List[ImageResponseDTO]


# Upload DTOs
class SingleImageUploadDTO(BaseModel):
    is_primary: bool = Field(False, description="Set as primary image")
    alt_text: Optional[str] = Field(None, max_length=255, description="Alt text for image")


class MultipleImageUploadDTO(BaseModel):
    primary_index: int = Field(0, ge=0, description="Index of image to set as primary")
    alt_texts: Optional[List[str]] = Field(None, description="Alt texts for images (optional)")

    @validator('alt_texts')
    def validate_alt_texts(cls, v):
        if v:
            for text in v:
                if text and len(text) > 255:
                    raise ValueError("Alt text cannot exceed 255 characters")
        return v


# Response DTOs
class ImageUploadResponseDTO(BaseModel):
    message: str
    image_id: int
    url: str
    is_primary: bool
    stadium_id: int


class MultipleImageUploadResponseDTO(BaseModel):
    message: str
    stadium_id: int
    total_uploaded: int
    uploaded_images: List[ImageUploadResponseDTO]
    failed_uploads: List[dict]


class ImageDeleteResponseDTO(BaseModel):
    message: str
    deleted_image_id: int


class SetPrimaryImageResponseDTO(BaseModel):
    message: str
    image_id: int
    stadium_id: int


# Stadium with Images DTO
class StadiumWithImagesDTO(BaseModel):
    id: int
    name: str
    description: Optional[str]
    address: str
    district: str
    latitude: Optional[float]
    longitude: Optional[float]
    price_per_hour: float
    height: float
    width: float
    size: str
    rating: float
    surface: str
    amenities: Optional[str]
    owner_id: int
    is_active: bool
    opening_hour: str
    closing_hour: str
    images: List[ImageResponseDTO]
    primary_image_url: Optional[str] = None
    total_images: int
    created_at: datetime
    updated_at: datetime

    @validator('primary_image_url', pre=True, always=True)
    def set_primary_image_url(cls, v, values):
        if 'images' in values:
            for img in values['images']:
                if img.is_primary:
                    return img.url
        return None

    @validator('total_images', pre=True, always=True)
    def set_total_images(cls, v, values):
        if 'images' in values:
            return len(values['images'])
        return 0

    class Config:
        from_attributes = True

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
    district: Optional[str] = None  # Added this missing field
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    price_per_hour: Optional[Decimal] = None
    height: Optional[Decimal] = None
    width: Optional[Decimal] = None
    size: Optional[StadiumSize] = None
    surface: Optional[SurfaceType] = None
    amenities: Optional[str] = None  # JSON string
    images: Optional[str] = None  # JSON string (not List[str])
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


class HourlyAvailability(BaseModel):
    hour: str  # "09:00", "10:00", etc.
    status: AvailabilityStatus  # GREEN or RED only
    is_available: bool


class HourlyAvailabilityResponse(BaseModel):
    stadium_id: int
    stadium_name: str
    date: date
    hourly_availability: List[HourlyAvailability]
    total_slots: int
    available_slots: int
