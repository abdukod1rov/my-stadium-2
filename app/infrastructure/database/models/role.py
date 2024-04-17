from sqlalchemy import Integer, ForeignKey, String, Text, Column, Table, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import BaseModel, Base

user_roles = Table(
    'user_roles', Base.metadata,

Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('user.id')),
    Column('role_id', Integer, ForeignKey('role.id')),
    PrimaryKeyConstraint('user_id', 'role_id')

)


class Role(BaseModel):
    __tablename__ = 'role'

    name: Mapped[str] = mapped_column(String(155), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    users = relationship("User", secondary=user_roles, back_populates='roles')
