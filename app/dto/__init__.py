"""
Data transfer object:
"""

from .types import Status
from .user import (User, UserWithPassword, UserLogin, UserInCreate,
                   UserOut, UserWithRoles, TgLogin)
from .base import Base
from .token import Token
from .todo import Todo, TodoEdit, TodoCreate, ToDoDelete
from .profile import ProfileBase, ProfileOut, ProfileCreate
from .role import RoleBase, RoleOut, RoleEdit, RoleCreate, Role
from .stadium import StadiumBase, StadiumCreate, UpdateStadium, FacilityCreate
