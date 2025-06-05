"""
Docstring:
Author: <Samandar Abdukodirov>
Email: <abdukodirovsamandar3@gmail.com>
Date: <2024>
License: <MIT>

Main router for stadium controller

"""
import asyncio
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import List

import aiofiles
from PIL import Image
from app import dto
from app.api.dependencies import get_current_user, dao_provider
from app.api.dependencies.authentication import get_admin_user
from app.api.dependencies.settings import BASE_DIR
from app.dto import User
from app.dto.stadium2 import StadiumUpdate, StadiumCreate
from app.dto.user import UserResponse
from app.infrastructure.database.dao.holder import HolderDao
from app.infrastructure.database.models.user import UserRole
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from typing import Optional
from fastapi.responses import FileResponse

MEDIA_DIR = BASE_DIR / 'media'
STADIUM_MEDIA_DIR = MEDIA_DIR / 'stadiums'
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
IMAGE_SIZES = {
    'thumbnail': (300, 200),
    'medium': (800, 600),
    'large': (1200, 800)
}

stadium_router = APIRouter(prefix="/api/v0/stadiums")
admin_router = APIRouter(prefix="/api/v0/admin")


@admin_router.get("/stadiums", description="List all stadiums created by admin")
async def admin_stadium_list(
        skip: int = 0,
        limit: int = 10,
        district: Optional[str] = Query(None),
        surface: Optional[str] = Query(None),
        size: Optional[str] = Query(None),
        dao: HolderDao = Depends(dao_provider)
):
    if district or surface or size:
        stadiums = await dao.stadium.search(district=district, surface=surface, size=size, skip=skip, limit=limit)
    else:
        stadiums = await dao.stadium._get_all(skip=skip, limit=limit)
    return stadiums


@stadium_router.get("/", description="List all stadiums")
async def stadium_list(
        skip: int = 0,
        limit: int = 10,
        district: Optional[str] = Query(None),
        surface: Optional[str] = Query(None),
        size: Optional[str] = Query(None),
        dao: HolderDao = Depends(dao_provider)
):
    if district or surface or size:
        stadiums = await dao.stadium.search(district=district, surface=surface, size=size, skip=skip, limit=limit)
    else:
        stadiums = await dao.stadium._get_all(skip=skip, limit=limit)
    return stadiums


@stadium_router.get("/{stadium_id}", description="Get stadium by ID")
async def stadium_detail(
        stadium_id: int,
        dao: HolderDao = Depends(dao_provider)
) -> dto.StadiumResponse:
    stadium = await dao.stadium._get_by_id(stadium_id)
    if not stadium:
        raise HTTPException(status_code=404, detail="Stadium not found")
    return stadium


@stadium_router.post("/", description="Create new stadium")
async def stadium_create(
        data: StadiumCreate,
        user: UserResponse = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    if user.role not in [UserRole.STADIUM_OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    stadium = await dao.stadium.create(stadium_data=data, owner_id=user.id)
    return stadium


@stadium_router.put("/{stadium_id}", description="Update stadium")
async def stadium_update(
        stadium_id: int,
        data: StadiumUpdate,
        user: UserResponse = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    stadium = await dao.stadium.update(stadium_id=stadium_id, stadium_data=data, owner_id=user.id)
    return stadium


@stadium_router.delete("/{stadium_id}", description="Delete stadium")
async def stadium_delete(
        stadium_id: int,
        user: UserResponse = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    # Check ownership
    stadium = await dao.stadium._get_by_id(stadium_id)
    if not stadium or (stadium.owner_id != user.id and user.role != UserRole.ADMIN):
        raise HTTPException(status_code=404, detail="Stadium not found or access denied")

    success = await dao.stadium._delete(stadium_id)
    if not success:
        raise HTTPException(status_code=404, detail="Stadium not found")
    return {"message": "Stadium deleted successfully"}


@stadium_router.get("/{stadium_id}/availability/daily", description="Get stadium daily availability")
async def stadium_daily_availability(
        stadium_id: int,
        dao: HolderDao = Depends(dao_provider)
):
    availability = await dao.stadium.get_weekly_availability(stadium_id)
    return availability


@stadium_router.get("/{stadium_id}/availability/hourly", description="Get stadium hourly availability")
async def stadium_hourly_availability(
        stadium_id: int,
        target_date: date = Query(..., description="Date to check availability (YYYY-MM-DD)"),
        dao: HolderDao = Depends(dao_provider)
):
    availability = await dao.stadium.get_hourly_availability(stadium_id, target_date)
    return availability


def validate_image_file(file: UploadFile) -> None:
    """Validate uploaded image file"""
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file provided"
        )

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )



# Admin Stadium Routes
@admin_router.get("/stadiums")
async def get_all_stadiums_admin(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        search: Optional[str] = None,
        status: Optional[str] = None,
        dao: HolderDao = Depends(dao_provider),
        admin: User = Depends(get_admin_user)
):
    """
    Get all stadiums with advanced filtering (Admin only)
    """
    stadiums = await dao.stadium.get_all_with_filters(
        skip=skip,
        limit=limit,
        search=search,
        status=status
    )
    total_count = await dao.stadium.count_with_filters(search=search, status=status)

    return {
        "stadiums": stadiums,
        "total": total_count,
        "page": skip // limit + 1,
        "pages": (total_count + limit - 1) // limit
    }


@admin_router.post("/stadiums")
async def create_stadium_admin(
        stadium_data: dto.StadiumCreate,
        dao: HolderDao = Depends(dao_provider),
        admin: User = Depends(get_admin_user)
):
    """
    Create new stadium (Admin only)
    """
    try:
        new_stadium = await dao.stadium.create(stadium_data)
        return {
            "message": "Stadium created successfully",
            "stadium": new_stadium
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error creating stadium: {str(e)}"
        )


@admin_router.put("/stadiums/{stadium_id}")
async def update_stadium_admin(
        stadium_id: int,
        stadium_data: dto.StadiumUpdate,
        dao: HolderDao = Depends(dao_provider),
        admin: User = Depends(get_admin_user)
):
    """
    Update stadium (Admin only)
    """
    stadium = await dao.stadium._get_by_id(stadium_id)
    if not stadium:
        raise HTTPException(
            status_code=404,
            detail=f"Stadium {stadium_id} not found"
        )

    try:
        updated_stadium = await dao.stadium.update(stadium_id, stadium_data)
        return {
            "message": "Stadium updated successfully",
            "stadium": updated_stadium
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error updating stadium: {str(e)}"
        )


@admin_router.delete("/stadiums/{stadium_id}")
async def delete_stadium_admin(
        stadium_id: int,
        dao: HolderDao = Depends(dao_provider),
        admin: User = Depends(get_admin_user)
):
    """
    Delete stadium (Admin only)
    """
    stadium = await dao.stadium._get_by_id(stadium_id)
    if not stadium:
        raise HTTPException(
            status_code=404,
            detail=f"Stadium {stadium_id} not found"
        )

    try:
        # Delete associated images first
        if stadium.image:
            image_path = Path(stadium.image)
            stadium_dir = BASE_DIR / image_path.parent
            if stadium_dir.exists():
                for file_path in stadium_dir.glob("*"):
                    if file_path.is_file():
                        file_path.unlink()
                if not any(stadium_dir.iterdir()):
                    stadium_dir.rmdir()

        # Delete stadium
        await dao.stadium.delete(stadium_id)

        return {"message": "Stadium deleted successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error deleting stadium: {str(e)}"
        )


# Admin Booking Routes
@admin_router.get("/bookings")
async def get_all_bookings_admin(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        status: Optional[str] = None,
        stadium_id: Optional[int] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        dao: HolderDao = Depends(dao_provider),
        admin: User = Depends(get_admin_user)
):
    """
    Get all bookings with advanced filtering (Admin only)
    """
    bookings = await dao.booking.get_all_with_filters(
        skip=skip,
        limit=limit,
        status=status,
        stadium_id=stadium_id,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    total_count = await dao.booking.count_with_filters(
        status=status,
        stadium_id=stadium_id,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )

    return {
        "bookings": bookings,
        "total": total_count,
        "page": skip // limit + 1,
        "pages": (total_count + limit - 1) // limit
    }


@admin_router.get("/bookings/{booking_id}")
async def get_booking_admin(
        booking_id: int,
        dao: HolderDao = Depends(dao_provider),
        admin: User = Depends(get_admin_user)
):
    """
    Get specific booking details (Admin only)
    """
    booking = await dao.booking._get_by_id(booking_id)
    if not booking:
        raise HTTPException(
            status_code=404,
            detail=f"Booking {booking_id} not found"
        )
    return booking


# @admin_router.put("/bookings/{booking_id}/status")
# async def update_booking_status_admin(
#         booking_id: int,
#         status_data: dto,
#         dao: HolderDao = Depends(dao_provider),
#         admin: User = Depends(get_admin_user)
# ):
#     """
#     Update booking status (Admin only)
#     """
#     booking = await dao.booking._get_by_id(booking_id)
#     if not booking:
#         raise HTTPException(
#             status_code=404,
#             detail=f"Booking {booking_id} not found"
#         )
#
#     try:
#         updated_booking = await dao.booking.update_status(booking_id, status_data)
#         return {
#             "message": "Booking status updated successfully",
#             "booking": updated_booking
#         }
#     except Exception as e:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Error updating booking status: {str(e)}"
#         )


@admin_router.delete("/bookings/{booking_id}")
async def cancel_booking_admin(
        booking_id: int,
        dao: HolderDao = Depends(dao_provider),
        admin: User = Depends(get_admin_user)
):
    """
    Cancel/Delete booking (Admin only)
    """
    booking = await dao.booking._get_by_id(booking_id)
    if not booking:
        raise HTTPException(
            status_code=404,
            detail=f"Booking {booking_id} not found"
        )

    try:
        await dao.booking.cancel(booking_id)
        return {"message": "Booking cancelled successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error cancelling booking: {str(e)}"
        )


@admin_router.get("/stats/dashboard")
async def get_admin_dashboard_stats(
        dao: HolderDao = Depends(dao_provider),
        admin: User = Depends(get_admin_user)
):
    """
    Get dashboard statistics for admin panel
    """
    stats = await dao.get_admin_stats()
    return {
        "total_stadiums": stats.get("total_stadiums", 0),
        "total_bookings": stats.get("total_bookings", 0),
        "total_users": stats.get("total_users", 0),
        "active_bookings": stats.get("active_bookings", 0),
        "revenue_this_month": stats.get("revenue_this_month", 0),
        "popular_stadiums": stats.get("popular_stadiums", [])
    }






# Export routers
__all__ = ["stadium_router", "admin_router"]
