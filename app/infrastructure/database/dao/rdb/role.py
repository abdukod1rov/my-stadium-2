from typing import Union

from pydantic import parse_obj_as
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.dao.rdb.base import BaseDAO
from app.infrastructure.database.models import Role as RoleModel
from app import dto


class RoleDAO(BaseDAO[RoleModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(RoleModel, session)

    async def add_role(self, role_data: dto.RoleCreate):
        role_dict = role_data.model_dump()
        result = await self.session.execute(insert(RoleModel).values(**role_dict
                                                                     ).returning(RoleModel))
        await self.session.commit()
        await self.session.flush()
        return dto.RoleOut.from_orm(result.scalar())

    async def get_role(self, role_id: int) -> dto.RoleOut:
        result = await self.session.execute(select(RoleModel).filter(
            RoleModel.id == role_id
        ))
        role = result.scalar()
        if role is not None:
            return dto.RoleOut.from_orm(role)

    async def get_role_by_name(self, name: str) -> Union[dto.RoleOut, None]:
        result = await self.session.execute(
            select(RoleModel).filter(RoleModel.name == name)
        )
        role = result.scalar()
        if role is not None:
            return dto.RoleOut.from_orm(role)
        return None

    async def get_roles(self) -> list[dto.RoleOut]:
        result = await self.session.execute(
            select(RoleModel)
        )
        return parse_obj_as(list[dto.RoleOut], result.scalars().all())

    async def edit_role(self, role_data: dto.RoleEdit, role_id: int):
        description = role_data.description if role_data.description else None

        result = await self.session.execute(
            update(RoleModel).values(
                name=role_data.name,
            ).filter(RoleModel.id == role_id).returning(RoleModel)
        )
        await self.session.commit()
        return dto.RoleOut.from_orm(result.scalar())
