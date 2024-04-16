from typing import Union

from pydantic import BaseModel, Field

from app.dto import Base
from .types import Status


class Todo(Base):
    name: str
    description: Union[str, None] = None
    status: Status


class TodoCreate(BaseModel):
    name: str
    description: Union[str, None] = None


class TodoEdit(BaseModel):
    todo_id: int
    name: str
    description: Union[str, None] = None
    status: Status


class ToDoDelete(BaseModel):
    todo_id: int
