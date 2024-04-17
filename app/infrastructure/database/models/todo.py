from app.infrastructure.database.models.base import BaseModel
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship, validates
from sqlalchemy import String, TIMESTAMP, Integer, ForeignKey, Text, Enum
from datetime import datetime
from sqlalchemy import text
from app import dto
from . import user


class Todo(BaseModel):
    __tablename__ = 'todo'

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    # status: Mapped[str] = mapped_column(Enum(dto.Status), nullable=False, server_default='new')
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    # user: Mapped['user.User'] = relationship(back_populates='todos')

    def __str__(self):
        return (f'{self.name}\n'
                f'{self.description}\n'
                f'{self.status}\n'
                f'{self.user_id}')
