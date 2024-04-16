from typing import Union

from pydantic import parse_obj_as
from sqlalchemy import insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto import TodoCreate, Status
from app.dto.user import UserInCreate, UserLogin
from app.infrastructure.database.dao.rdb.base import BaseDAO, Model
from app.infrastructure.database.models.todo import Todo as ToDoModel
from app import dto


class ToDoDAO(BaseDAO[ToDoModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(ToDoModel, session)

    # Initialize model here from BaseDAO

    async def add_todo(self, todo_data: TodoCreate, user_id: int):
        todo_dict = todo_data.model_dump()
        result = await self.session.execute(insert(ToDoModel).values(**todo_dict, user_id=user_id, status=Status.NEW
                                                                     ).returning(ToDoModel))
        await self.session.commit()
        await self.session.flush()
        return dto.Todo.from_orm(result.scalar())

    async def get_todo(self, too_id: int, user_id: int) -> dto.Todo:
        result = await self.session.execute(select(ToDoModel).filter(
            ToDoModel.id == too_id, ToDoModel.user_id == user_id
        ))
        todo = result.scalar()
        if todo is not None:
            return dto.Todo.from_orm(todo)

    async def get_todo_by_name(self, name: str) -> Union[dto.Todo, None]:
        result = await self.session.execute(
            select(ToDoModel).filter(ToDoModel.name == name)
        )
        todo = result.scalar()
        if todo is not None:
            return dto.Todo.from_orm(todo)
        return None

    async def get_todos(self, user_id: int) -> list[dto.Todo]:
        result = await self.session.execute(
            select(ToDoModel).filter(ToDoModel.user_id == user_id)
        )
        return parse_obj_as(list[dto.Todo], result.scalars().all())

    async def edit_todo(self, todo_data: dto.TodoEdit):
        todo_dict = todo_data.model_dump()
        result = await self.session.execute(
            update(ToDoModel).values(
                name=todo_data.name,
                description=todo_data.description,
                status=todo_data.status
            ).filter(ToDoModel.id == todo_data.todo_id).returning(ToDoModel)
        )
        await self.session.commit()
        return dto.Todo.from_orm(result.scalar())
