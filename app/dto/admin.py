from datetime import datetime
from typing import List

from pydantic import BaseModel

from app.dto import UserOut, UserResponse
from app.dto.stadium import StadiumOut


class StadiumAdminRequest(BaseModel):
    user_id: int
    stadium_id: int


class StadiumAdminResponse(BaseModel):
    user_id: int
    stadium_id: int
    user: UserResponse
    stadium_name: str
    added_at: datetime


class AdminListResponse(BaseModel):
    stadium_id: int
    stadium_name: str
    admins: List[UserResponse]
    total_admins: int


class UserStadiumsResponse(BaseModel):
    user_id: int
    user_name: str
    stadiums: List[StadiumOut]
    total_stadiums: int