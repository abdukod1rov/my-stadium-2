from fastapi import FastAPI
from .user import router as authentication_router
from .todo import router as todo_router
from .stadium import router as stadium_router


def setup(app: FastAPI) -> None:
    app.include_router(
        router=authentication_router,
        tags=["Authentication"]
    )
    # app.include_router(
    #     router=todo_router,
    #     tags=['ToDo']
    # )
    app.include_router(
        router=stadium_router,
        tags=['Stadium']
    )
