from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.dao.rdb import UserDAO, ToDoDAO, ProfileDAO
from app.infrastructure.database.dao.rdb.base import BaseDAO
from app.infrastructure.database.dao.rdb.role import RoleDAO


class HolderDao:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.base = BaseDAO
        self.user = UserDAO(session=self.session)
        self.todo = ToDoDAO(session=self.session)
        self.profile = ProfileDAO(session=self.session)
        self.role = RoleDAO(session=self.session)

