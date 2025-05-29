from typing import Type, Sequence, Any, Coroutine

from sqlalchemy import insert, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.dto.user import UserInCreate
from app.infrastructure.database.dao.rdb import BaseDAO
from app.infrastructure.database.models import UserModel
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
        return result.scalar()


    async def get_user_with_stadiums(self, phone_number: str):
        result = await self.session.execute(select(UserModel).options(joinedload(UserModel.role)).options(joinedload(
            UserModel.owned_stadiums
        )).filter(
            self.model.phone_number == phone_number
        ))
        user = result.scalar()
        if user is not None:
            return dto.UserOut.from_orm(user)

    async def get_user(self, phone_number: str):
        result = await self.session.execute(select(UserModel).filter(
            self.model.phone_number == phone_number
        ))
        return result.scalar_one_or_none()

    async def get_user_by_tg_id(self, tg_id: int):
        result = await self.session.execute(select(UserModel).filter(
            UserModel.tg_id == tg_id
        ))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int):
        result = await self.session.execute(select(UserModel)
        .options(joinedload(UserModel.owned_stadiums))
        .filter(
            UserModel.id == user_id
        ))
        return result.unique().scalar()

    async def get_users(self) -> Sequence[UserModel]:
        result = await self.session.execute(
            select(UserModel)
        )
        return result.scalars().all()


