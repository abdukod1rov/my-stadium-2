from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import update

from app.api.dependencies import dao_provider, get_current_user
from app.dto import UserResponse
from app.dto.booking import BookingCreate
from app.infrastructure.database.dao.holder import HolderDao
from app.infrastructure.database.models import BookingModel
from app.infrastructure.database.models.booking import BookingStatus
from app.infrastructure.database.models.user import UserRole

booking_router = APIRouter(prefix="/bookings")


@booking_router.get("/", description="Get user's bookings")
async def booking_list(
        skip: int = 0,
        limit: int = 10,
        user: UserResponse = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    bookings = await dao.booking.get_by_user(user_id=user.id, skip=skip, limit=limit)
    return bookings


@booking_router.get("/{booking_id}", description="Get booking by ID")
async def booking_detail(
        booking_id: int,
        user: UserResponse = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    booking = await dao.booking._get_by_id(booking_id)
    if not booking or booking.user_id != user.id:
        raise HTTPException(status_code=404, detail="Booking not found or access denied")
    return booking


@booking_router.post("/", description="Create new booking")
async def booking_create(
        data: BookingCreate,
        user: UserResponse = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    booking = await dao.booking.create(booking_data=data, user_id=user.id)
    return booking


@booking_router.put("/{booking_id}/cancel", description="Cancel booking")
async def booking_cancel(
        booking_id: int,
        user: UserResponse = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    booking = await dao.booking.update_status(booking_id=booking_id, status=BookingStatus.CANCELLED, user_id=user.id)
    return booking


@booking_router.put("/{booking_id}/confirm", description="Confirm booking")
async def booking_confirm_user(
        booking_id: int,
        user: UserResponse = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    booking = await dao.booking.confirm_booking(booking_id=booking_id, user_id=user.id)
    return booking


@booking_router.get("/stadium/{stadium_id}", description="Get stadium bookings (owner only)")
async def stadium_bookings(
        stadium_id: int,
        skip: int = 0,
        limit: int = 10,
        user: UserResponse = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    # Check if user owns the stadium
    stadium = await dao.stadium._get_by_id(stadium_id)
    if not stadium or (stadium.owner_id != user.id and user.role != UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Access denied")

    bookings = await dao.booking.get_by_stadium(stadium_id=stadium_id, skip=skip, limit=limit)
    return bookings