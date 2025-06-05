from fastapi import FastAPI
from .user import router as user_router
from .stadium import stadium_router
from .admin import router as admin_router
from .booking import booking_router
from .auth import router as auth_router
from .stadium_image import stadium_image_router


def setup(app: FastAPI) -> None:
    app.include_router(
        router=auth_router,
        tags=['Authentication']
    )
    app.include_router(
        router=user_router,
        tags=["Users"]
    )
    app.include_router(
        router=booking_router,
        tags=["Booking"]
    )
    app.include_router(
        router=stadium_router,
        tags=['Stadium']
    )
    app.include_router(
        router=admin_router,
        tags=['Admin']
    )
    app.include_router(
        router=stadium_image_router,
        tags=['Stadium Image']
    )
