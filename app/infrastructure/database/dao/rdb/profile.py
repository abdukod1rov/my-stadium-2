from sqlalchemy import insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.dto.user import UserInCreate, UserLogin
from app.infrastructure.database.dao.rdb.base import BaseDAO, Model
from app.infrastructure.database.models import UserProfile, User
from app.infrastructure.database.models import User as UserModel
from app import dto


class ProfileDAO(BaseDAO[UserProfile]):
    def __init__(self, session: AsyncSession):
        super().__init__(UserProfile, session)

    async def get_profile_by_user(self, user_id: int):
        result = await self.session.execute(select(UserProfile).options(joinedload(UserProfile.user)).
                                            filter(UserProfile.user_id == user_id)
                                            )
        user_profile = result.scalar_one_or_none()
        return user_profile

    async def create_profile(self, user_id: int):
        result = await self.session.execute(insert(UserProfile).values(
            user_id=user_id
        ).returning(UserProfile))
        await self.session.commit()
        await self.session.flush()
        return result.scalar()

    async def edit_profile(self, user_id: int, profile_data: dto.ProfileBase):
        profile_dict = profile_data.model_dump(exclude_unset=True)
        result = await self.session.execute(update(UserProfile).values(**profile_dict).
                                            filter(UserProfile.user_id == user_id).returning(UserProfile))
        await self.session.commit()
        return dto.ProfileOut.from_orm(result.scalar())

    async def edit_photo(self, user_id: int, photo_path):
        result = await self.session.execute(update(UserProfile).values(
            photo=photo_path
        ).filter(UserProfile.user_id == user_id).returning(UserProfile))
        await self.session.commit()
        return dto.ProfileOut.from_orm(result.scalar())
