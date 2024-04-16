import re
from typing import List

from app.infrastructure.database.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, validates, relationship
from sqlalchemy import String, TIMESTAMP, Integer
from datetime import datetime
from sqlalchemy import text

from app.infrastructure.database.models.todo import Todo


class User(BaseModel):
    __tablename__ = 'user'

    tg_id: Mapped[int] = mapped_column(Integer, nullable=True, unique=True)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    username: Mapped[str] = mapped_column(String(155), nullable=True, unique=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str] = mapped_column(String(50), nullable=True)
    password: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(server_default='True', nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)
    last_login: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    is_superuser: Mapped[bool] = mapped_column(server_default='False', nullable=False)
    is_staff: Mapped[bool] = mapped_column(server_default='False', nullable=False)

    # todos: Mapped[List['Todo']] = relationship(
    #     back_populates='user', cascade='all, delete-orphan'
    # )

    @validates('email')
    def validate_email(self, key, email):
        # assert len(email) > 10
        # assert @ in mail
        if email is not None:
            if '@' not in email:
                raise ValueError('invalid email address, bor togirla')
            return email

    @validates('phone_number')
    def validate_phone(self, key, phone_number):
        """
        Example phone number --> 8908211633

        """
        pattern = r'^8\d{9}'
        pattern = r'^8\d{9}$'
        if not re.match(pattern, phone_number):
            raise ValueError('invalid phone number')
        return phone_number

    def __repr__(self):
        return f'User(id={self.id!r}, phone={self.phone_number!r}, fullname={self.first_name!r} {self.last_name})'
