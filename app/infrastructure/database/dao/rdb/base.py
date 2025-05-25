import logging
from typing import (
    List,
    TypeVar,
    Type,
    Generic, Any, Sequence
)

from fastapi import HTTPException
from sqlalchemy import delete, func, Row, RowMapping, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm.strategy_options import Load
from app.infrastructure.database.models import Base

Model = TypeVar("Model", Base, Base)

logger = logging.getLogger(__name__)

class BaseDAO(Generic[Model]):

    def __init__(self, model, session: AsyncSession):
        self.model = model
        self.session = session

    async def _get_all(self, skip: int = 0, limit: int = 10):
        try:
            result = await self.session.execute(
                select(self.model).offset(skip).limit(limit)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get all {self.model.__name__}: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")

    async def _get_by_id(self, id: int):
        try:
            result = await self.session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get {self.model.__name__} by id: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")

    async def _delete(self, id: int):
        try:
            result = await self.session.execute(
                delete(self.model).where(self.model.id == id)
            )
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Failed to delete {self.model.__name__}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete record")

    async def count(
            self,
    ):
        result = await self.session.execute(select(func.count(self.model.id)))
        return result.scalar_one()

    async def commit(
            self,
    ):
        await self.session.commit()

    async def _flush(self, *objects):
        await self.session.flush(objects)


