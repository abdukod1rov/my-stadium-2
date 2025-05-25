import enum

from app.infrastructure.database.models.base import BaseModel
from sqlalchemy.orm import relationship
from sqlalchemy import (
     Integer, Column, Text, ForeignKey,
    Enum as SQLEnum, DateTime, Numeric,
)
from datetime import datetime


class AvailabilityStatus(str, enum.Enum):
    GREEN = "green"    # Very few bookings (0-2 per day)
    YELLOW = "yellow"  # Normal bookings (3-5 per day)
    RED = "red"

class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    EXPIRED = "expired"


class BookingModel(BaseModel):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stadium_id = Column(Integer, ForeignKey("stadiums.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    status = Column(SQLEnum(BookingStatus), default=BookingStatus.PENDING)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("UserModel", back_populates="bookings")
    stadium = relationship("StadiumModel", back_populates="bookings")