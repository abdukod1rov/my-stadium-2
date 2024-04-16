from fastapi import APIRouter, Depends, HTTPException

from app import dto
from app.api.dependencies import get_user, dao_provider
from app.infrastructure.database.dao.holder import HolderDao

router = APIRouter(prefix="/todo")


@router.get(
    path="/all",
    description="Get all todos"
)
async def get_todos(
        user: dto.user = Depends(get_user),
        dao: HolderDao = Depends(dao_provider)
) -> list[dto.Todo]:
    user_object = await user  # Await the user dependency to get the user object
    return await dao.todo.get_todos(user_id=user_object.id)


@router.post(
    path="/new",
    description="Create a new todo",
)
async def new_todo(
        todo_data: dto.TodoCreate,
        user: dto.user = Depends(get_user),
        dao: HolderDao = Depends(dao_provider),
) -> dto.Todo:
    user_object = await user
    todo_db = await dao.todo.get_todo_by_name(todo_data.name)
    if todo_db is not None:
        raise HTTPException(
            detail=f'Todo {todo_data.name} already exists',
            status_code=400
        )
    return await dao.todo.add_todo(todo_data, user_id=user_object.id)


@router.patch(
    path="/edit",
    description="Create a new todo",
)
async def edit_todo(
        todo_data: dto.TodoEdit,
        user: dto.user = Depends(get_user),
        dao: HolderDao = Depends(dao_provider),
) -> dto.Todo:
    user_object = await user
    if await dao.todo.get_todo(too_id=todo_data.todo_id, user_id=user_object.id) is None:
        raise HTTPException(
            detail=f"Todo '{todo_data.todo_id}' does not exist",
            status_code=404
        )
    return await dao.todo.edit_todo(todo_data)
