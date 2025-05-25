import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional
from redis import asyncio as redis_asyncio

from fastapi import HTTPException
from sqlalchemy import select, insert, and_, or_, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.util import await_only

from app.api.dependencies.settings import get_redis_connection
from app.dto.booking import BookingCreate
from app.infrastructure.database.dao.rdb import BaseDAO
from app.infrastructure.database.models import BookingModel, StadiumModel
from app.infrastructure.database.models.booking import BookingStatus

logger = logging.getLogger(__name__)


class BookingDAO(BaseDAO):
    def __init__(self, session: AsyncSession):
        super().__init__(BookingModel, session)

    async def create(self, booking_data: BookingCreate, user_id: int,
                     ) -> BookingModel:
        try:
            # Check if stadium exists
            stadium = await self.session.execute(
                select(StadiumModel).where(StadiumModel.id == booking_data.stadium_id)
            )
            stadium = stadium.scalar_one_or_none()
            if not stadium:
                raise HTTPException(status_code=404, detail="Stadium not found")

            # Check availability
            if not await self._check_availability(booking_data.stadium_id,
                                                  booking_data.start_time,
                                                  booking_data.end_time):
                raise HTTPException(status_code=409, detail="Stadium not available for selected time")

            # Calculate total price
            duration_hours = (booking_data.end_time - booking_data.start_time).total_seconds() / 3600
            total_price = stadium.price_per_hour * Decimal(str(duration_hours))

            booking_dict = booking_data.model_dump()
            booking_dict.update({
                'user_id': user_id,
                'total_price': total_price
            })

            result = await self.session.execute(
                insert(BookingModel).values(**booking_dict).returning(BookingModel)
            )
            await self.session.commit()
            booking = result.scalar()

            # Set Redis expiration for booking confirmation (10 minutes)
            await self._set_booking_expiration(booking.id)

            return booking
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Failed to create booking: {e}")
            raise HTTPException(status_code=500, detail="Failed to create booking")

    async def _set_booking_expiration(self, booking_id: int):
        """Set booking expiration in Redis (10 minutes)"""
        redis_client = await get_redis_connection()
        try:
            expiration_key = f"booking_expiration:{booking_id}"
            await redis_client.setex(expiration_key, 600, "pending")  # 600 seconds = 10 minutes

            # Schedule background task to check expiration
            asyncio.create_task(self._check_booking_expiration(booking_id))
        except Exception as e:
            logger.error(f"Failed to set booking expiration in Redis: {e}")

    async def _check_booking_expiration(self, booking_id: int):
        """Background task to check and expire bookings"""
        redis_client = await get_redis_connection()
        try:
            await asyncio.sleep(600)  # Wait 10 minutes

            expiration_key = f"booking_expiration:{booking_id}"
            if await redis_client.exists(expiration_key):
                # Check if booking is still pending
                booking = await self._get_by_id(booking_id)
                if booking and booking.status == BookingStatus.PENDING:
                    # Expire the booking
                    await self.session.execute(
                        update(BookingModel)
                        .where(BookingModel.id == booking_id)
                        .values(status=BookingStatus.EXPIRED)
                    )
                    await self.session.commit()
                    logger.info(f"Booking {booking_id} expired due to no confirmation")

                # Remove from Redis
                await redis_client.delete(expiration_key)
        except Exception as e:
            logger.error(f"Failed to check booking expiration: {e}")

    async def confirm_booking(self, booking_id: int, user_id: int) -> Optional[BookingModel]:
        """Confirm booking and remove from Redis expiration"""
        try:
            booking = await self._get_by_id(booking_id)
            if not booking:
                raise HTTPException(status_code=404, detail="Booking not found")

            if booking.status != BookingStatus.PENDING:
                raise HTTPException(status_code=400, detail="Booking cannot be confirmed")

            # Update booking status
            await self.session.execute(
                update(BookingModel)
                .where(BookingModel.id == booking_id)
                .values(status=BookingStatus.CONFIRMED)
            )
            await self.session.commit()

            # Remove from Redis expiration
            expiration_key = f"booking_expiration:{booking_id}"
            redis_client = await get_redis_connection()
            await redis_client.delete(expiration_key)

            return await self._get_by_id(booking_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Failed to confirm booking: {e}")
            raise HTTPException(status_code=500, detail="Failed to confirm booking")

    async def _check_availability(self, stadium_id: int, start_time: datetime, end_time: datetime) -> bool:
        try:
            result = await self.session.execute(
                select(BookingModel).where(
                    and_(
                        BookingModel.stadium_id == stadium_id,
                        BookingModel.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING]),
                        or_(
                            and_(BookingModel.start_time <= start_time, BookingModel.end_time > start_time),
                            and_(BookingModel.start_time < end_time, BookingModel.end_time >= end_time),
                            and_(BookingModel.start_time >= start_time, BookingModel.end_time <= end_time)
                        )
                    )
                )
            )
            conflicting_bookings = result.scalars().all()
            return len(conflicting_bookings) == 0
        except SQLAlchemyError as e:
            logger.error(f"Failed to check availability: {e}")
            return False

    async def update_status(self, booking_id: int, status: BookingStatus, user_id: int) -> Optional[BookingModel]:
        try:
            # Check if booking exists and belongs to user
            existing = await self._get_by_id(booking_id)
            if not existing or existing.user_id != user_id:
                raise HTTPException(status_code=404, detail="Booking not found or access denied")

            await self.session.execute(
                update(BookingModel)
                .where(BookingModel.id == booking_id)
                .values(status=status)
            )
            await self.session.commit()
            return await self._get_by_id(booking_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Failed to update booking status: {e}")
            raise HTTPException(status_code=500, detail="Failed to update booking")

    async def get_by_user(self, user_id: int, skip: int = 0, limit: int = 10):
        try:
            result = await self.session.execute(
                select(BookingModel)
                .where(BookingModel.user_id == user_id)
                .offset(skip).limit(limit)
                .order_by(BookingModel.created_at.desc())
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get bookings by user: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")

    async def get_by_stadium(self, stadium_id: int, skip: int = 0, limit: int = 10):
        try:
            result = await self.session.execute(
                select(BookingModel)
                .where(BookingModel.stadium_id == stadium_id)
                .offset(skip).limit(limit)
                .order_by(BookingModel.start_time.desc())
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get bookings by stadium: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")
