from typing import Type

from pydantic import parse_obj_as
from sqlalchemy import insert, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.user import UserInCreate, UserLogin
from app.infrastructure.database.dao.rdb.base import BaseDAO, Model
from app.infrastructure.database.models import User as UserModel
from app import dto


class UserDAO(BaseDAO[UserModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(UserModel, session)

    # Initialize model here from BaseDAO

    async def add_user(self, user_data: UserInCreate):
        user_dict = user_data.model_dump()
        result = await self.session.execute(insert(UserModel).values(**user_dict
                                                                     ).returning(UserModel))
        await self.session.commit()
        await self.session.flush()
        return dto.UserOut.from_orm(result.scalar())

    async def get_user_with_password(self, user_data: UserLogin) -> dto.User:
        user_dict = user_data.model_dump()
        result = await self.session.execute(select(UserModel).filter(
            UserModel.phone_number == user_dict.get('phone_number')
        ))
        user = result.scalar()
        if user is not None:
            return dto.UserWithPassword.from_orm(user)

    async def get_user(self, phone_number: str):
        result = await self.session.execute(select(UserModel).filter(
            self.model.phone_number == phone_number
        ))
        user = result.scalar()
        if user is not None:
            return dto.UserOut.from_orm(user)

    async def get_user_by_id(self, user_id: int):
        result = await self.session.execute(select(UserModel).filter(
            self.model.id == user_id
        ))
        user = result.scalar()
        if user is not None:
            return dto.UserOut.from_orm(user)

    async def get_users(self):
        result = await self.session.execute(
            select(UserModel)
        )
        return parse_obj_as(list[dto.UserOut], result.scalars().all())
