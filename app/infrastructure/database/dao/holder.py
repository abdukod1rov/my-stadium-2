from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.dao.rdb import UserDAO, BookingDAO
from app.infrastructure.database.dao.rdb.base import BaseDAO
from app.infrastructure.database.dao.rdb.stadium import StadiumDAO


class HolderDao:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.base = BaseDAO
        self.user = UserDAO(session=self.session)
        self.stadium = StadiumDAO(session=self.session)
        self.booking = BookingDAO(session=self.session)
