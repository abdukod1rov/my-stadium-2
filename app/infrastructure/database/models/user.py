import enum
import re

from app.infrastructure.database.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, validates, relationship, Relationship
from sqlalchemy import String, TIMESTAMP, Integer, Column, Enum as SQLEnum, Boolean, DateTime
import datetime
from sqlalchemy import text

class UserRole(str, enum.Enum):
    CLIENT = "client"
    ADMIN = "admin"
    STADIUM_OWNER = "stadium_owner"

class UserModel(BaseModel):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tg_id: Mapped[int] = mapped_column(Integer, nullable=True, unique=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20))
    role = Column(SQLEnum(UserRole), default=UserRole.CLIENT)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC).replace(tzinfo=None))
    updated_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
                        onupdate=datetime.datetime.now(datetime.UTC).replace(tzinfo=None))

    # Relationships
    owned_stadiums = relationship("StadiumModel", back_populates="owner")
    bookings = relationship("BookingModel", back_populates="user")


# class User(BaseModel):
#     __tablename__ = 'users'
#
#     tg_id: Mapped[int] = mapped_column(Integer, nullable=True, unique=True)
#     phone_number: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
#     password: Mapped[str] = mapped_column(nullable=True)
#     is_active: Mapped[bool] = mapped_column(server_default=text('true'), nullable=False)
#     # email: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)
#     last_login: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
#     is_superuser: Mapped[bool] = mapped_column(server_default=text('false'), nullable=False)
#     is_staff: Mapped[bool] = mapped_column(server_default=text('false'), nullable=False)
#
#     stadiums = Relationship('Stadium', back_populates='owner', uselist=True, passive_deletes=True)
#     roles = Relationship('Role', secondary='user_roles', passive_deletes=True, back_populates='users')
#
#     @validates('email')
#     def validate_email(self, key, email):
#         # assert len(email) > 10
#         # assert @ in mail
#         if email is not None:
#             if '@' not in email:
#                 raise ValueError('invalid email address')
#             return email
#
#     @validates('phone_number')
#     def validate_phone(self, key, phone_number):
#         """
#         Example phone number --> 8908211633
#
#         """
#         pattern = r'^8\d{9}'
#         pattern = r'^8\d{9}$'
#         if not re.match(pattern, phone_number):
#             raise ValueError('invalid phone number')
#         return phone_number
#
#     def __repr__(self):
#         return f'User(id={self.id!r}, phone={self.phone_number!r}, roles: {self.roles})'
