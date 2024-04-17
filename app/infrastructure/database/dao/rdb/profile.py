from sqlalchemy import insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.user import UserInCreate, UserLogin
from app.infrastructure.database.dao.rdb.base import BaseDAO, Model
from app.infrastructure.database.models import UserProfile
from app.infrastructure.database.models import User as UserModel
from app import dto


class ProfileDAO(BaseDAO[UserProfile]):
    def __init__(self, session: AsyncSession):
        super().__init__(UserProfile, session)

    async def create_profile(self, user_id: int):
        result = await self.session.execute(insert(UserProfile).values(
            user_id=user_id
        ).returning(UserProfile))
        await self.session.commit()
        await self.session.flush()
        return dto.ProfileOut.from_orm(result.scalar())

    async def get_profile(self, user_id: int):
        result = await self.session.execute(select(
            UserProfile).filter(UserProfile.user_id == user_id))
        profile = result.scalar()
        if profile is not None:
            return dto.ProfileOut.from_orm(profile)

    async def edit_profile(self, user_id: int, profile_data: dto.ProfileBase):
        profile_dict = profile_data.model_dump()
        result = await self.session.execute(update(UserProfile).values(
            first_name=profile_data.first_name,
            last_name=profile_data.last_name,
            bio=profile_data.bio,
            photo=profile_data.photo
        ).filter(UserProfile.user_id == user_id).returning(UserProfile))
        await self.session.commit()
        return dto.ProfileOut.from_orm(result.scalar())

    async def edit_photo(self, user_id: int, photo_path):
        result = await self.session.execute(update(UserProfile).values(
            photo=photo_path
        ).filter(UserProfile.user_id == user_id).returning(UserProfile))
        await self.session.commit()
        return dto.ProfileOut.from_orm(result.scalar())
