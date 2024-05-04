from typing import List

from sqlalchemy import Integer, ForeignKey, String, Text, Column, Table, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, Relationship

from app.infrastructure.database.models.base import BaseModel, Base


# user_role_associate_table = Table(
#     'user_roles', Base.metadata,
#     Column('user_id', Integer, ForeignKey('user.id')),
#     Column('role_id', Integer, ForeignKey('role.id')),
#     PrimaryKeyConstraint('user_id', 'role_id')
#
# )

class UserRole(Base):
    __tablename__ = 'user_roles'

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)


class Role(BaseModel):
    __tablename__ = 'roles'

    name: Mapped[str] = mapped_column(String(155), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    # users = Relationship('User', secondary='user_roles', back_populates='roles')
    users = Relationship('User', secondary='user_roles', back_populates='roles',
                         passive_deletes=True)

    def __repr__(self):
        return f"{self.name}"

    def __str__(self):
        return f"{self.name}"
