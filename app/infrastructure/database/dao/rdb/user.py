from typing import Type, Sequence

from sqlalchemy import insert, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.dto.user import UserInCreate, UserLogin
from app.infrastructure.database.dao.rdb import BaseDAO
from app.infrastructure.database.models import User as UserModel, Role, User, UserProfile
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

    async def get_user_with_password(self, user_data: UserLogin) -> dto.User:
        result = await self.session.execute(select(UserModel).filter(
            UserModel.phone_number == user_data.username
        ))
        return result.scalar_one_or_none()

    async def get_user_with_stadiums(self, phone_number: str):
        result = await self.session.execute(select(UserModel).options(joinedload(UserModel.roles)).options(joinedload(
            UserModel.stadiums
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
        .options(joinedload(UserModel.roles))
        .options(joinedload(UserModel.stadiums))
        .filter(
            UserModel.id == user_id
        ))
        return result.unique().scalar()

    async def get_users(self) -> Sequence[User]:
        result = await self.session.execute(
            select(UserModel)
        )
        # roles_result = await self.session.execute(
        #     select(UserModel)
        # )
        # print('result: ', roles_result.scalars().all())
        # users = result.scalars().all()
        # print(users)
        return result.scalars().all()

    async def assign_role(self, user_id: int, role_name: str):
        role = await self.get_role_by_name(role_name)
        user = await self.get_user_by_id(user_id)

        if role is not None and user is not None:
            from app.infrastructure.database.models import UserRole
            existing_association = await self.session.execute(
                select(UserRole).filter(UserRole.user_id == user.id, UserRole.role_id == role.id))
            result = existing_association.scalar_one_or_none()
            if result is None:
                print('no association found')
                # Create a new association record
                association = insert(UserRole).values(user_id=user.id, role_id=role.id)
                print(association)
                result2 = await self.session.execute(association)
                await self.session.flush()
                await self.session.commit()
                return {"message": f"Role {role.name} assigned to {user.phone_number} successfully"}
            else:
                return {'error': 'already assigned'}
        return {"message": "Role not found"}

    async def get_role_by_name(self, role_name: str):
        result = await self.session.execute(select(Role).filter(
            Role.name == role_name))
        return result.scalar_one_or_none()

    async def remove_role(self, user_id: int, role: Role):
        result = await self.session.execute(
            text(f"DELETE FROM user_roles WHERE user_id={user_id} AND role_id={role.id}")
        )
        await self.session.commit()
        return result

    async def get_profile_by_user_id(self, user_id: int):
        result = await self.session.execute(select(UserProfile).filter(UserProfile.user_id == user_id))
        return result.scalar_one_or_none()
