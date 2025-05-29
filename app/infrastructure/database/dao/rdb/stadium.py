from datetime import date, timedelta, datetime
from typing import Union, Sequence, Optional

from fastapi import HTTPException
from pydantic import parse_obj_as
from sqlalchemy import insert, select, update, func, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto import StadiumCreate, StadiumUpdate
from app.dto.stadium2 import StadiumAvailabilityResponse, WeeklyAvailability, HourlyAvailability, \
    HourlyAvailabilityResponse
from app.infrastructure.database.dao.rdb import UserDAO
from app.infrastructure.database.dao.rdb.base import BaseDAO
from app.infrastructure.database.models import StadiumModel, BookingModel, UserModel
from app import dto
import logging

from app.infrastructure.database.models.booking import BookingStatus, AvailabilityStatus
from app.infrastructure.database.models.stadium import stadium_admins

logger = logging.getLogger(__name__)


class StadiumDAO(BaseDAO):
    def __init__(self, session: AsyncSession):
        super().__init__(StadiumModel, session)

    async def create(self, stadium_data: StadiumCreate, owner_id: int) -> StadiumModel:
        try:
            stadium_dict = stadium_data.model_dump()
            result = await self.session.execute(
                insert(StadiumModel).values(**stadium_dict, owner_id=owner_id).returning(StadiumModel)
            )
            await self.session.commit()
            return result.scalar()
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Failed to create stadium: {e}")
            raise HTTPException(status_code=500, detail="Failed to create stadium")

    async def update(self, stadium_id: int, stadium_data: StadiumUpdate, user: UserModel) -> Optional[StadiumModel]:
        try:
            existing = await self._get_by_id(stadium_id)
            if not existing:
                raise HTTPException(status_code=404, detail="Stadium not found")

            # Check if user is owner, admin of this stadium, or super admin
            is_owner = existing.owner_id == user.id
            is_super_admin = user.role == "admin"

            # Check if user is admin of this stadium
            is_stadium_admin = False
            if not (is_owner or is_super_admin):
                admin_check = await self.session.execute(
                    select(stadium_admins).where(
                        and_(
                            stadium_admins.c.user_id == user.id,
                            stadium_admins.c.stadium_id == stadium_id
                        )
                    )
                )
                is_stadium_admin = admin_check.fetchone() is not None

            if not (is_owner or is_super_admin or is_stadium_admin):
                raise HTTPException(status_code=403, detail="Access denied")

            update_data = {k: v for k, v in stadium_data.model_dump().items() if v is not None}
            if not update_data:
                return existing

            await self.session.execute(
                update(StadiumModel)
                .where(StadiumModel.id == stadium_id)
                .values(**update_data)
            )
            await self.session.commit()
            return await self._get_by_id(stadium_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Failed to update stadium: {e}")
            raise HTTPException(status_code=500, detail="Failed to update stadium")

    async def get_by_owner(self, owner_id: int, skip: int = 0, limit: int = 10):
        try:
            result = await self.session.execute(
                select(StadiumModel)
                .where(StadiumModel.owner_id == owner_id)
                .offset(skip).limit(limit)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get stadiums by owner: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")

    async def get_weekly_availability(self, stadium_id: int) -> StadiumAvailabilityResponse:
        try:
            stadium = await self._get_by_id(stadium_id)
            if not stadium:
                raise HTTPException(status_code=404, detail="Stadium not found")

            # Get next 7 days starting from tomorrow
            start_date = date.today() + timedelta(days=1)
            weekly_data = []

            for i in range(7):
                current_date = start_date + timedelta(days=i)
                weekday_name = current_date.strftime("%A")

                # Get bookings count for this date
                result = await self.session.execute(
                    select(func.count(BookingModel.id))
                    .where(
                        and_(
                            BookingModel.stadium_id == stadium_id,
                            BookingModel.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING]),
                            func.date(BookingModel.start_time) == current_date
                        )
                    )
                )
                booking_count = result.scalar() or 0

                # Calculate available slots (assuming 1-hour slots from opening to closing)
                opening_time = datetime.strptime(stadium.opening_hour, "%H:%M").time()
                closing_time = datetime.strptime(stadium.closing_hour, "%H:%M").time()
                total_hours = (datetime.combine(current_date, closing_time) -
                               datetime.combine(current_date, opening_time)).seconds // 3600
                available_slots = max(0, total_hours - booking_count)

                # Determine status based on booking count
                if booking_count <= 2:
                    status = AvailabilityStatus.GREEN
                elif booking_count <= 5:
                    status = AvailabilityStatus.YELLOW
                else:
                    status = AvailabilityStatus.RED

                weekly_data.append(WeeklyAvailability(
                    date=current_date,
                    weekday=weekday_name,
                    status=status,
                    booking_count=booking_count,
                    available_slots=available_slots
                ))

            return StadiumAvailabilityResponse(
                stadium_id=stadium_id,
                stadium_name=stadium.name,
                weekly_availability=weekly_data
            )
        except SQLAlchemyError as e:
            logger.error(f"Failed to get weekly availability: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")

    async def get_hourly_availability(self, stadium_id: int, target_date: date) -> HourlyAvailabilityResponse:
        try:
            stadium = await self._get_by_id(stadium_id)
            if not stadium:
                raise HTTPException(status_code=404, detail="Stadium not found")

            # Don't allow checking past dates
            if target_date < date.today():
                raise HTTPException(status_code=400, detail="Cannot check availability for past dates")

            # Get all bookings for the target date
            result = await self.session.execute(
                select(BookingModel.start_time, BookingModel.end_time)
                .where(
                    and_(
                        BookingModel.stadium_id == stadium_id,
                        BookingModel.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING]),
                        func.date(BookingModel.start_time) == target_date
                    )
                )
            )
            bookings = result.fetchall()
            print("Bookins for the week", bookings)

            # Parse stadium operating hours
            opening_time = datetime.strptime(stadium.opening_hour, "%H:%M").time()
            closing_time = datetime.strptime(stadium.closing_hour, "%H:%M").time()

            # Generate hourly slots
            hourly_data = []
            current_hour = datetime.combine(target_date, opening_time)
            end_datetime = datetime.combine(target_date, closing_time)

            while current_hour < end_datetime:
                slot_end = current_hour + timedelta(hours=1)

                # Check if this hour slot conflicts with any booking
                is_booked = False
                for booking in bookings:
                    booking_start = booking.start_time
                    booking_end = booking.end_time

                    # Check for overlap: slot overlaps with booking if:
                    # slot_start < booking_end AND slot_end > booking_start
                    if current_hour < booking_end and slot_end > booking_start:
                        is_booked = True
                        break

                # Determine status: GREEN if available, RED if booked
                status = AvailabilityStatus.RED if is_booked else AvailabilityStatus.GREEN

                hourly_data.append(HourlyAvailability(
                    hour=current_hour.strftime("%H:%M"),
                    status=status,
                    is_available=not is_booked
                ))

                current_hour = slot_end

            return HourlyAvailabilityResponse(
                stadium_id=stadium_id,
                stadium_name=stadium.name,
                date=target_date,
                hourly_availability=hourly_data,
                total_slots=len(hourly_data),
                available_slots=sum(1 for slot in hourly_data if slot.is_available)
            )

        except SQLAlchemyError as e:
            logger.error(f"Failed to get hourly availability: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")