from typing import Union, Sequence

from fastapi import HTTPException
from pydantic import parse_obj_as
from sqlalchemy import insert, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto import StadiumCreate, UpdateStadium
from app.infrastructure.database.dao.rdb.base import BaseDAO
from app.infrastructure.database.models import Stadium as StadiumModel, Facility
from app import dto
import logging

logger = logging.getLogger(__name__)


class StadiumDAO(BaseDAO[StadiumModel]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(StadiumModel, session)

    async def create(self, stadium_data: StadiumCreate, owner_id: int) -> StadiumModel:
        try:
            stadium_dict = stadium_data.model_dump()
            result = await self.session.execute(
                insert(StadiumModel).values(**stadium_dict, owner_id=owner_id).returning(StadiumModel))
            await self.session.flush()
            await self.session.commit()
            return result.scalar()
        except SQLAlchemyError as e:
            # Roll back the transaction
            await self.session.rollback()
            # Log the exception for debugging purposes
            logger.error(f"Failed to create stadium: {e}")
            # Raise appropriate HTTP exception with error message
            raise HTTPException(status_code=500, detail="Failed to create stadium. Please try again later.")

    async def update(self, stadium_id: int, stadium_data: UpdateStadium):
        stadium_dict = stadium_data.model_dump(exclude_unset=True)
        # noinspection PyTypeChecker
        result = await self.session.execute(
            update(StadiumModel).values(**stadium_dict).returning(StadiumModel)
            .filter(
                StadiumModel.id == stadium_id)
        )
        await self.session.flush()
        await self.session.commit()
        return result.scalar()

    async def create_facility(self, facility_data: dto.FacilityCreate):
        facility_dict = facility_data.model_dump(exclude_unset=True)
        try:
            result = await self.session.execute(insert(Facility).values(*facility_dict))
            await self.session.flush()
            await self.session.commit()
            return result.scalar()
        except SQLAlchemyError as err:
            await self.session.rollback()
            raise Exception(str(err))

    async def get_facility(self, facility_id: int):
        result = await self.session.execute(select(Facility).filter(
            Facility.id == facility_id
        ))
        return result.scalar_one_or_none()

    async def get_facilities(self, offset: int = 0, limit: int = 20):
        result = await self.session.execute(select(
            Facility
        ).offset(offset).limit(limit))
        return result.scalars()
