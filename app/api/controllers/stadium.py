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


def generate_unique_filename(original_filename: str) -> str:
    """Generate unique filename with UUID"""
    file_ext = Path(original_filename).suffix.lower()
    unique_id = str(uuid.uuid4())
    return f"{unique_id}{file_ext}"


async def save_image_with_variants(
        file_content: bytes,
        stadium_name: str,
        filename: str
) -> dict:
    """Save image in multiple sizes"""
    stadium_dir = STADIUM_MEDIA_DIR / stadium_name
    stadium_dir.mkdir(parents=True, exist_ok=True)

    saved_files = {}

    # Save original image
    original_path = stadium_dir / filename
    async with aiofiles.open(original_path, 'wb') as f:
        await f.write(file_content)

    saved_files['original'] = f"media/stadiums/{stadium_name}/{filename}"

    # Create resized variants
    try:
        with Image.open(original_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            for size_name, dimensions in IMAGE_SIZES.items():
                # Create resized image
                resized_img = img.copy()
                resized_img.thumbnail(dimensions, Image.Resampling.LANCZOS)

                # Generate filename for variant
                name_without_ext = Path(filename).stem
                ext = Path(filename).suffix
                variant_filename = f"{name_without_ext}_{size_name}{ext}"
                variant_path = stadium_dir / variant_filename

                # Save variant
                resized_img.save(variant_path, quality=85, optimize=True)
                saved_files[size_name] = f"media/stadiums/{stadium_name}/{variant_filename}"

    except Exception as e:
        # If image processing fails, clean up and raise error
        for path in saved_files.values():
            full_path = BASE_DIR / path
            if full_path.exists():
                full_path.unlink()
        raise HTTPException(
            status_code=400,
            detail=f"Error processing image: {str(e)}"
        )

    return saved_files


# Stadium Photo Routes
@stadium_router.post("/images/{stadium_id}")
async def add_stadium_photos(
        stadium_id: int,
        files: List[UploadFile] = File(...),
        dao: HolderDao = Depends(dao_provider),
        user: User = Depends(get_current_user)
):
    """
    Add multiple photos to a stadium with automatic resizing and optimization
    """
    # Check if files list is not empty
    if not files or len(files) == 0:
        raise HTTPException(
            status_code=400,
            detail="No files provided"
        )

    # Limit number of files per upload
    MAX_FILES_PER_UPLOAD = 10
    if len(files) > MAX_FILES_PER_UPLOAD:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files. Maximum {MAX_FILES_PER_UPLOAD} files allowed per upload"
        )

    # Get stadium
    stadium = await dao.stadium._get_by_id(stadium_id)
    if not stadium:
        raise HTTPException(
            status_code=404,
            detail=f"Stadium {stadium_id} not found"
        )

    # Generate safe stadium name
    stadium_name = str(stadium.name).replace(" ", "_").lower()
    stadium_name = "".join(c for c in stadium_name if c.isalnum() or c in ['_', '-'])

    uploaded_images = []
    failed_uploads = []
    total_size = 0

    # Validate all files first
    for i, file in enumerate(files):
        try:
            validate_image_file(file)

            # Check individual file size
            if file.size and file.size > MAX_FILE_SIZE:
                failed_uploads.append({
                    "filename": file.filename,
                    "error": f"File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)}MB"
                })
                continue

            total_size += file.size if file.size else 0

        except HTTPException as e:
            failed_uploads.append({
                "filename": file.filename,
                "error": e.detail
            })

    # Check total upload size (50MB limit for batch upload)
    MAX_TOTAL_SIZE = 50 * 1024 * 1024  # 50MB
    if total_size > MAX_TOTAL_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Total upload size too large. Maximum: {MAX_TOTAL_SIZE // (1024 * 1024)}MB"
        )

    # Process valid files
    valid_files = [f for f in files if not any(fail['filename'] == f.filename for fail in failed_uploads)]

    if not valid_files:
        raise HTTPException(
            status_code=400,
            detail="No valid image files to upload"
        )

    # Process files concurrently with semaphore to limit concurrent operations
    semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent file operations

    async def process_single_file(file: UploadFile):
        async with semaphore:
            try:
                unique_filename = generate_unique_filename(file.filename)
                content = await file.read()

                # Save image variants
                saved_files = await save_image_with_variants(content, stadium_name, unique_filename)

                return {
                    "original_filename": file.filename,
                    "unique_filename": unique_filename,
                    "images": saved_files,
                    "size": len(content)
                }

            except Exception as e:
                failed_uploads.append({
                    "filename": file.filename,
                    "error": str(e)
                })
                return None

    # Process all files concurrently
    tasks = [process_single_file(file) for file in valid_files]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter successful uploads
    successful_uploads = [result for result in results if result is not None and not isinstance(result, Exception)]

    # Handle exceptions
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            failed_uploads.append({
                "filename": valid_files[i].filename,
                "error": str(result)
            })

    if not successful_uploads:
        # Clean up any partially uploaded files
        stadium_dir = STADIUM_MEDIA_DIR / stadium_name
        if stadium_dir.exists():
            for file_path in stadium_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail="All file uploads failed"
        )

    try:
        import json

        # Get existing images from stadium (parse JSON string)
        existing_images = []
        if stadium.images:
            try:
                existing_images = json.loads(stadium.images) if isinstance(stadium.images, str) else stadium.images
                if not isinstance(existing_images, list):
                    existing_images = []
            except (json.JSONDecodeError, TypeError):
                existing_images = []

        # Add new image data to existing ones
        for upload in successful_uploads:
            image_data = {
                "original_filename": upload["original_filename"],
                "unique_filename": upload["unique_filename"],
                "paths": upload["images"],
                "size": upload["size"],
                "uploaded_at": datetime.utcnow().isoformat(),
                "uploaded_by": user.id
            }
            existing_images.append(image_data)

        # Convert back to JSON string for storage
        images_json = json.dumps(existing_images)

        # Update stadium with new images JSON
        update_stadium = dto.StadiumUpdate(images=images_json)
        updated_stadium = await dao.stadium.update(stadium_id, update_stadium, user)

        return {
            "message": f"Successfully uploaded {len(successful_uploads)} images",
            "stadium": updated_stadium,
            "uploaded_images": successful_uploads,
            "failed_uploads": failed_uploads if failed_uploads else None,
            "summary": {
                "total_files": len(files),
                "successful": len(successful_uploads),
                "failed": len(failed_uploads)
            }
        }

    except Exception as e:
        # Clean up uploaded files on database error
        stadium_dir = STADIUM_MEDIA_DIR / stadium_name
        for upload in successful_uploads:
            for image_path in upload["images"].values():
                full_path = BASE_DIR / image_path
                if full_path.exists():
                    full_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Error updating stadium with images: {str(e)}"
        )


@stadium_router.post("/image/{stadium_id}")
async def add_single_stadium_photo(
        stadium_id: int,
        file: UploadFile = File(...),
        dao: HolderDao = Depends(dao_provider),
        user: User = Depends(get_current_user)
):
    """
    Add a single photo to a stadium (legacy endpoint)
    """
    # Call the multiple upload endpoint with single file
    return await add_stadium_photos(stadium_id, [file], dao, user)


@stadium_router.get("/images/{stadium_id}")
async def get_stadium_photos(
        stadium_id: int,
        dao: HolderDao = Depends(dao_provider)
):
    """
    Get all stadium photos information
    """
    stadium = await dao.stadium._get_by_id(stadium_id)
    if not stadium:
        raise HTTPException(
            status_code=404,
            detail="Stadium not found"
        )

    images = []
    if stadium.images:
        try:
            import json
            stadium_images = json.loads(stadium.images) if isinstance(stadium.images, str) else stadium.images

            for i, image_data in enumerate(stadium_images):
                if isinstance(image_data, dict):
                    # New format with full image data
                    paths = image_data.get("paths", {})
                    image_info = {
                        "id": i,
                        "original_filename": image_data.get("original_filename"),
                        "unique_filename": image_data.get("unique_filename"),
                        "size": image_data.get("size"),
                        "uploaded_at": image_data.get("uploaded_at"),
                        "uploaded_by": image_data.get("uploaded_by"),
                        "urls": {
                            "thumbnail": f"/v0/stadiums/image/{stadium_id}/file?index={i}&size=thumbnail",
                            "medium": f"/v0/stadiums/image/{stadium_id}/file?index={i}&size=medium",
                            "large": f"/v0/stadiums/image/{stadium_id}/file?index={i}&size=large",
                            "original": f"/v0/stadiums/image/{stadium_id}/file?index={i}&size=original"
                        },
                        "paths": paths
                    }
                    images.append(image_info)
                else:
                    # Legacy format - just image path string
                    image_info = {
                        "id": i,
                        "path": image_data,
                        "urls": {
                            "thumbnail": f"/v0/stadiums/image/{stadium_id}/file?index={i}&size=thumbnail",
                            "medium": f"/v0/stadiums/image/{stadium_id}/file?index={i}&size=medium",
                            "large": f"/v0/stadiums/image/{stadium_id}/file?index={i}&size=large",
                            "original": f"/v0/stadiums/image/{stadium_id}/file?index={i}&size=original"
                        }
                    }
                    images.append(image_info)

        except (json.JSONDecodeError, TypeError) as e:
            # Handle malformed JSON
            return {
                "stadium_id": stadium_id,
                "total_images": 0,
                "images": [],
                "error": "Invalid images data format"
            }

    return {
        "stadium_id": stadium_id,
        "total_images": len(images),
        "images": images
    }


@stadium_router.get("/image/{stadium_id}/file")
async def get_stadium_photo_file(
        stadium_id: int,
        index: int = Query(..., description="Image index in the images array"),
        size: str = Query("medium", regex="^(thumbnail|medium|large|original)$"),
        dao: HolderDao = Depends(dao_provider)
):
    """
    Get stadium photo file by index in specified size
    """
    stadium = await dao.stadium._get_by_id(stadium_id)
    if not stadium:
        raise HTTPException(
            status_code=404,
            detail="Stadium not found"
        )

    if not stadium.images:
        raise HTTPException(
            status_code=404,
            detail="No images found for this stadium"
        )

    try:
        import json
        stadium_images = json.loads(stadium.images) if isinstance(stadium.images, str) else stadium.images

        if index >= len(stadium_images) or index < 0:
            raise HTTPException(
                status_code=404,
                detail="Image index out of range"
            )

        image_data = stadium_images[index]

        # Handle both new format (dict) and legacy format (string)
        if isinstance(image_data, dict):
            # New format with paths object
            paths = image_data.get("paths", {})
            image_path = paths.get(size, paths.get("original"))
        else:
            # Legacy format - just image path string
            image_path = image_data

            # For legacy format, construct size-specific path
            if size != "original":
                path_obj = Path(image_path)
                name_without_ext = path_obj.stem
                ext = path_obj.suffix
                sized_filename = f"{name_without_ext}_{size}{ext}"
                sized_path = path_obj.parent / sized_filename
                image_path = str(sized_path)

        if not image_path:
            raise HTTPException(
                status_code=404,
                detail=f"Image size '{size}' not found"
            )

        full_path = BASE_DIR / image_path

        if not full_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Image file not found on disk"
            )

        return FileResponse(full_path)

    except (json.JSONDecodeError, TypeError):
        raise HTTPException(
            status_code=500,
            detail="Invalid images data format"
        )


@stadium_router.get("/image/{stadium_id}")
async def get_stadium_primary_photo(
        stadium_id: int,
        size: str = Query("medium", regex="^(thumbnail|medium|large|original)$"),
        dao: HolderDao = Depends(dao_provider)
):
    """
    Get stadium primary photo in specified size (legacy endpoint)
    """
    stadium = await dao.stadium._get_by_id(stadium_id)
    if not stadium or not stadium.image:
        raise HTTPException(
            status_code=404,
            detail="Stadium or primary image not found"
        )

    return await get_stadium_photo_file(stadium_id, stadium.image, size, dao)


@stadium_router.delete("/images/{stadium_id}")
async def delete_stadium_photos(
        stadium_id: int,
        image_paths: Optional[List[str]] = None,
        dao: HolderDao = Depends(dao_provider),
        user: User = Depends(get_current_user)
):
    """
    Delete specific stadium photos or all photos if no paths specified
    """
    stadium = await dao.stadium._get_by_id(stadium_id)
    if not stadium:
        raise HTTPException(
            status_code=404,
            detail=f"Stadium {stadium_id} not found"
        )

    # Get current images
    current_images = []
    if hasattr(stadium, 'images') and stadium.images:
        current_images = stadium.images if isinstance(stadium.images, list) else [stadium.images]

    if stadium.image and stadium.image not in current_images:
        current_images.append(stadium.image)

    if not current_images:
        raise HTTPException(
            status_code=404,
            detail="No images found for this stadium"
        )

    # Determine which images to delete
    if image_paths is None:
        # Delete all images
        images_to_delete = current_images.copy()
        remaining_images = []
    else:
        # Delete specific images
        images_to_delete = [path for path in image_paths if path in current_images]
        remaining_images = [path for path in current_images if path not in images_to_delete]

        if not images_to_delete:
            raise HTTPException(
                status_code=404,
                detail="No valid images found to delete"
            )

    deleted_count = 0
    failed_deletions = []

    try:
        # Delete image files
        for image_path in images_to_delete:
            try:
                # Delete all variants of the image
                path_obj = Path(image_path)
                stadium_dir = BASE_DIR / path_obj.parent
                base_filename = path_obj.stem

                # Remove size suffixes to get original filename
                for size in ['_thumbnail', '_medium', '_large']:
                    base_filename = base_filename.replace(size, '')

                # Delete all variants
                for size_suffix in ['', '_thumbnail', '_medium', '_large']:
                    variant_filename = f"{base_filename}{size_suffix}{path_obj.suffix}"
                    variant_path = stadium_dir / variant_filename

                    if variant_path.exists():
                        variant_path.unlink()

                deleted_count += 1

            except Exception as e:
                failed_deletions.append({
                    "path": image_path,
                    "error": str(e)
                })

        # Update stadium with remaining images
        update_data = {}

        if hasattr(stadium, 'images'):
            update_data["images"] = remaining_images if remaining_images else None

        # Update primary image if it was deleted
        if stadium.image in images_to_delete:
            new_primary = remaining_images[0] if remaining_images else None
            update_data["image"] = new_primary

        if update_data:
            update_stadium = dto.StadiumUpdate(**update_data)
            await dao.stadium.update(stadium_id, update_data)

        # Clean up empty directories
        stadium_name = str(stadium.name).replace(" ", "_").lower()
        stadium_name = "".join(c for c in stadium_name if c.isalnum() or c in ['_', '-'])
        stadium_dir = STADIUM_MEDIA_DIR / stadium_name

        if stadium_dir.exists() and not any(stadium_dir.iterdir()):
            stadium_dir.rmdir()

        return {
            "message": f"Successfully deleted {deleted_count} images",
            "deleted_count": deleted_count,
            "remaining_images": remaining_images,
            "failed_deletions": failed_deletions if failed_deletions else None
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting photos: {str(e)}"
        )


@stadium_router.delete("/image/{stadium_id}")
async def delete_stadium_photo(
        stadium_id: int,
        dao: HolderDao = Depends(dao_provider),
        user: User = Depends(get_current_user)
):
    """
    Delete stadium primary photo (legacy endpoint)
    """
    return await delete_stadium_photos(stadium_id, None, dao, user)


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
