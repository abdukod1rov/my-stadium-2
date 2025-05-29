import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete, and_

from app.api.dependencies import get_current_user, dao_provider
from app.dto import UserOut, UserResponse
from app.dto.admin import StadiumAdminResponse, StadiumAdminRequest, AdminListResponse, UserStadiumsResponse
from app.dto.stadium import StadiumOut
from app.infrastructure.database.dao.holder import HolderDao
from app.infrastructure.database.models import UserModel
from app.infrastructure.database.models.stadium import stadium_admins, StadiumModel

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post(
    "/stadiums/add-admin",
    response_model=StadiumAdminResponse,
    description="Add an admin to a stadium (Only stadium owner or super admin)"
)
async def add_stadium_admin(
        request: StadiumAdminRequest,
        current_user: UserModel = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    # Check if stadium exists
    stadium = await dao.stadium._get_by_id(request.stadium_id)
    if not stadium:
        raise HTTPException(
            status_code=404,
            detail="Stadium not found"
        )

    # Check permissions: stadium owner or super admin
    if stadium.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only stadium owner or super admin can add admins"
        )

    # Check if user exists
    user_to_add = await dao.user.get_user_by_id(request.user_id)
    if not user_to_add:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Check if user is already an admin of this stadium
    existing_admin = await dao.session.execute(
        select(stadium_admins).where(
            and_(
                stadium_admins.c.user_id == request.user_id,
                stadium_admins.c.stadium_id == request.stadium_id
            )
        )
    )
    if existing_admin.fetchone():
        raise HTTPException(
            status_code=400,
            detail="User is already an admin of this stadium"
        )

    # Add admin relationship
    await dao.session.execute(
        stadium_admins.insert().values(
            user_id=request.user_id,
            stadium_id=request.stadium_id
        )
    )
    await dao.session.commit()

    return StadiumAdminResponse(
        user_id=request.user_id,
        stadium_id=request.stadium_id,
        user=UserResponse.model_validate(user_to_add),
        stadium_name=stadium.name,
        added_at=datetime.datetime.now(datetime.UTC)
    )


# Remove admin from stadium
@router.delete(
    "/stadiums/remove",
    description="Remove an admin from a stadium"
)
async def remove_stadium_admin(
        request: StadiumAdminRequest,
        current_user: UserModel = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    # Check if stadium exists
    stadium = await dao.stadium._get_by_id(request.stadium_id)
    if not stadium:
        raise HTTPException(
            status_code=404,
            detail="Stadium not found"
        )

    # Check permissions: stadium owner or super admin
    if stadium.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only stadium owner or super admin can remove admins"
        )

    # Check if admin relationship exists
    existing_admin = await dao.session.execute(
        select(stadium_admins).where(
            and_(
                stadium_admins.c.user_id == request.user_id,
                stadium_admins.c.stadium_id == request.stadium_id
            )
        )
    )
    if not existing_admin.fetchone():
        raise HTTPException(
            status_code=404,
            detail="User is not an admin of this stadium"
        )

    # Remove admin relationship
    await dao.session.execute(
        delete(stadium_admins).where(
            and_(
                stadium_admins.c.user_id == request.user_id,
                stadium_admins.c.stadium_id == request.stadium_id
            )
        )
    )
    await dao.session.commit()

    return {"message": "Admin removed successfully"}


# Get all admins of a stadium
@router.get(
    "/stadiums/{stadium_id}/admins",
    response_model=AdminListResponse,
    description="Get all admins of a specific stadium"
)
async def get_stadium_admins(
        stadium_id: int,
        current_user: UserModel = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    # Check if stadium exists
    stadium = await dao.stadium._get_by_id(stadium_id)
    if not stadium:
        raise HTTPException(
            status_code=404,
            detail="Stadium not found"
        )

    # Check permissions: stadium owner, admin of this stadium, or super admin
    is_owner = stadium.owner_id == current_user.id
    is_super_admin = current_user.role == "admin"

    # Check if current user is admin of this stadium
    is_stadium_admin = False
    if not (is_owner or is_super_admin):
        admin_check = await dao.session.execute(
            select(stadium_admins).where(
                and_(
                    stadium_admins.c.user_id == current_user.id,
                    stadium_admins.c.stadium_id == stadium_id
                )
            )
        )
        is_stadium_admin = admin_check.fetchone() is not None

    if not (is_owner or is_super_admin or is_stadium_admin):
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    # Get all admins
    result = await dao.session.execute(
        select(UserModel)
        .join(stadium_admins, UserModel.id == stadium_admins.c.user_id)
        .where(stadium_admins.c.stadium_id == stadium_id)
        .order_by(UserModel.first_name)
    )
    admins = result.scalars().all()

    return AdminListResponse(
        stadium_id=stadium_id,
        stadium_name=stadium.name,
        admins=[UserOut.model_validate(admin) for admin in admins],
        total_admins=len(admins)
    )


# Get all stadiums where user is admin
@router.get(
    "/stadiums/user/{user_id}",
    response_model=UserStadiumsResponse,
    description="Get all stadiums where a user is admin"
)
async def get_user_admin_stadiums(
        user_id: int,
        current_user: UserModel = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    # Check permissions: self, or super admin
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    # Check if user exists
    user = await dao.user.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Get all stadiums where user is admin
    result = await dao.session.execute(
        select(StadiumModel)
        .join(stadium_admins, StadiumModel.id == stadium_admins.c.stadium_id)
        .where(stadium_admins.c.user_id == user_id)
        .order_by(StadiumModel.name)
    )
    stadiums = result.scalars().all()

    return UserStadiumsResponse(
        user_id=user_id,
        user_name=f"{user.first_name} {user.last_name}".strip(),
        stadiums=[StadiumOut.from_orm(stadium) for stadium in stadiums],
        total_stadiums=len(stadiums)
    )


# Get current user's admin stadiums
@router.get(
    "/my-stadiums",
    response_model=UserStadiumsResponse,
    description="Get stadiums where current user is admin"
)
async def get_my_admin_stadiums(
        current_user: UserModel = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    return await get_user_admin_stadiums(current_user.id, current_user, dao)


# Bulk add admins to stadium
# @router.post(
#     "stadiums/{stadium_id}/bulk-add",
#     description="Add multiple admins to a stadium"
# )
# async def bulk_add_stadium_admins(
#         stadium_id: int,
#         user_ids: List[int],
#         current_user: UserModel = Depends(get_current_user),
#         dao: HolderDao = Depends(dao_provider)
# ):
#     # Check if stadium exists
#     stadium = await dao.stadium._get_by_id(stadium_id)
#     if not stadium:
#         raise HTTPException(
#             status_code=404,
#             detail="Stadium not found"
#         )
#
#     # Check permissions
#     if stadium.owner_id != current_user.id and current_user.role != "admin":
#         raise HTTPException(
#             status_code=403,
#             detail="Only stadium owner or super admin can add admins"
#         )
#
#     successful_adds = []
#     failed_adds = []
#
#     for user_id in user_ids:
#         try:
#             # Check if user exists
#             user = await dao.user.get_user_by_id(user_id)
#             if not user:
#                 failed_adds.append({"user_id": user_id, "reason": "User not found"})
#                 continue
#
#             # Check if already admin
#             existing = await dao.session.execute(
#                 select(stadium_admins).where(
#                     and_(
#                         stadium_admins.c.user_id == user_id,
#                         stadium_admins.c.stadium_id == stadium_id
#                     )
#                 )
#             )
#             if existing.fetchone():
#                 failed_adds.append({"user_id": user_id, "reason": "Already admin"})
#                 continue
#
#             # Add admin
#             await dao.session.execute(
#                 stadium_admins.insert().values(
#                     user_id=user_id,
#                     stadium_id=stadium_id
#                 )
#             )
#             successful_adds.append(user_id)
#
#         except Exception as e:
#             failed_adds.append({"user_id": user_id, "reason": str(e)})
#
#     await dao.session.commit()
#
#     return {
#         "message": f"Successfully added {len(successful_adds)} admins",
#         "successful_adds": successful_adds,
#         "failed_adds": failed_adds,
#         "summary": {
#             "total_requested": len(user_ids),
#             "successful": len(successful_adds),
#             "failed": len(failed_adds)
#         }
#     }


# Check if user is admin of stadium
@router.get(
    "/stadiums/{stadium_id}/check/{user_id}",
    description="Check if a user is admin of a stadium"
)
async def check_stadium_admin(
        stadium_id: int,
        user_id: int,
        current_user: UserModel = Depends(get_current_user),
        dao: HolderDao = Depends(dao_provider)
):
    # Basic permission check
    if current_user.id != user_id and current_user.role != "admin":
        # Allow stadium owners to check their stadium admins
        stadium = await dao.stadium._get_by_id(stadium_id)
        if not stadium or stadium.owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

    # Check admin status
    result = await dao.session.execute(
        select(stadium_admins).where(
            and_(
                stadium_admins.c.user_id == user_id,
                stadium_admins.c.stadium_id == stadium_id
            )
        )
    )
    is_admin = result.fetchone() is not None

    return {
        "user_id": user_id,
        "stadium_id": stadium_id,
        "is_admin": is_admin
    }