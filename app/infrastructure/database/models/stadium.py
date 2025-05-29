import enum

from app.infrastructure.database.models.base import BaseModel, Base
from sqlalchemy.orm import Mapped, mapped_column, validates, relationship, Relationship
from sqlalchemy import (
    String, TIMESTAMP, Integer, Column, Text, ForeignKey,
    Float, Enum as SQLEnum, TIME, JSON, DateTime, DECIMAL, Numeric, Boolean, Table,
)

import datetime

"""
Pivot table that holds information from 2 tables No
No need for id column as it is a pivot table
"""


class SurfaceType(str, enum.Enum):
    GRASS = "grass"
    ARTIFICIAL_TURF = "artificial_turf"
    CONCRETE = "concrete"

class StadiumSize(str, enum.Enum):
    FIVE_V_FIVE = "5v5"
    SEVEN_V_SEVEN = "7v7"
    ELEVEN_V_ELEVEN = "11v11"


stadium_admins = Table(
    "stadium_admins",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("stadium_id", ForeignKey("stadiums.id"), primary_key=True)
)


class StadiumModel(BaseModel):
    __tablename__ = "stadiums"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    address = Column(Text, nullable=False)
    district = Column(String(100), nullable=False)
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    price_per_hour = Column(Numeric(10, 2), nullable=False)
    height = Column(Numeric(5, 2), nullable=False)  # Stadium height in meters
    width = Column(Numeric(5, 2), nullable=False)
    size = Column(SQLEnum(StadiumSize), nullable=False)
    rating = Column(Numeric(5, 2), default=0.0)
    surface = Column(SQLEnum(SurfaceType), nullable=False)
    amenities = Column(Text)  # JSON string of amenities
    images = Column(Text)  # JSON string of image URLs
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    opening_hour = Column(String(5), default="06:00")  # HH:MM format
    closing_hour = Column(String(5), default="23:00")  # HH:MM format
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC).replace(tzinfo=None))
    updated_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
                        onupdate=datetime.datetime.now(datetime.UTC).replace(tzinfo=None))

    # Relationships
    owner = relationship("UserModel", back_populates="owned_stadiums")
    bookings = relationship("BookingModel", back_populates="stadium")
    admins = relationship(
        "UserModel",
        secondary="stadium_admins",
        back_populates="admin_stadiums"
    )

