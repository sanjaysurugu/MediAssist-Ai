from pathlib import Path
from typing import List, Optional
from uuid import UUID
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.department import Department
from app.models.profile import DoctorProfile, PatientProfile
from app.models.user import User, UserAvatar, UserRole
from app.schemas.profile import DoctorProfileOut, DoctorProfileUpdate, PatientProfileOut, PatientProfileUpdate
from app.schemas.user import UserOut, UserUpdate
from app.services.audit_service import log_action

router = APIRouter()
AVATAR_DIRECTORY = Path(__file__).resolve().parents[4] / "uploads" / "avatars"
MAX_AVATAR_SIZE = 2 * 1024 * 1024
AVATAR_TYPES = {
    "image/jpeg": (".jpg", lambda content: content.startswith(b"\xff\xd8\xff")),
    "image/png": (".png", lambda content: content.startswith(b"\x89PNG\r\n\x1a\n")),
    "image/webp": (".webp", lambda content: content.startswith(b"RIFF") and content[8:12] == b"WEBP"),
}


@router.post("/me/avatar", response_model=UserOut)
async def upload_my_avatar(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    content_type = (file.content_type or "").lower()
    avatar_type = AVATAR_TYPES.get(content_type)
    if avatar_type is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Upload a JPEG, PNG, or WebP image."
        )

    content = await file.read(MAX_AVATAR_SIZE + 1)
    if len(content) > MAX_AVATAR_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Profile photos must be 2 MB or smaller."
        )
    extension, signature_matches = avatar_type
    if not signature_matches(content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file does not match its image type."
        )

    filename = f"{current_user.id}-{uuid.uuid4().hex}{extension}"

    previous_filename = current_user.avatar_url
    current_user.avatar_url = filename
    avatar = db.query(UserAvatar).filter(UserAvatar.user_id == current_user.id).first()
    if avatar is None:
        avatar = UserAvatar(user_id=current_user.id)
        db.add(avatar)
    avatar.content_type = content_type
    avatar.image_data = content
    db.commit()
    db.refresh(current_user)

    if previous_filename and Path(previous_filename).name == previous_filename:
        previous_file = AVATAR_DIRECTORY / previous_filename
        if previous_file.is_file():
            previous_file.unlink()

    log_action(
        db=db,
        action="PROFILE_PHOTO_UPDATE",
        resource="users",
        resource_id=str(current_user.id),
        user_id=current_user.id,
        request=request
    )
    return current_user


@router.get("/{user_id}/avatar")
def get_user_avatar(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if current_user.id != target_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot view this profile photo.")
    if not target_user.avatar_url or Path(target_user.avatar_url).name != target_user.avatar_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile photo not found.")

    avatar = db.query(UserAvatar).filter(UserAvatar.user_id == target_user.id).first()
    if avatar:
        return Response(
            content=avatar.image_data,
            media_type=avatar.content_type,
            headers={"Cache-Control": "private, no-store"}
        )

    avatar_path = AVATAR_DIRECTORY / target_user.avatar_url
    if not avatar_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile photo not found.")
    media_type = {
        ".jpg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(avatar_path.suffix.lower())
    if not media_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile photo not found.")
    return FileResponse(
        avatar_path,
        media_type=media_type,
        headers={"Cache-Control": "private, no-store"}
    )


@router.delete("/me/avatar", response_model=UserOut)
def delete_my_avatar(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    previous_filename = current_user.avatar_url
    current_user.avatar_url = None
    avatar = db.query(UserAvatar).filter(UserAvatar.user_id == current_user.id).first()
    if avatar:
        db.delete(avatar)
    db.commit()
    db.refresh(current_user)

    if previous_filename and Path(previous_filename).name == previous_filename:
        previous_file = AVATAR_DIRECTORY / previous_filename
        if previous_file.is_file():
            previous_file.unlink()

    log_action(
        db=db,
        action="PROFILE_PHOTO_DELETE",
        resource="users",
        resource_id=str(current_user.id),
        user_id=current_user.id,
        request=request
    )
    return current_user


@router.put("/me/profile/patient", response_model=PatientProfileOut)
def update_patient_profile(
    profile_in: PatientProfileUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.PATIENT]))
):
    """
    Patient Endpoint: Update own profile info.
    """
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == current_user.id).first()
    if not profile:
        profile = PatientProfile(user_id=current_user.id)
        db.add(profile)
        db.flush()

    update_data = profile_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    log_action(
        db=db,
        action="PROFILE_UPDATE_PATIENT",
        resource="patient_profiles",
        resource_id=str(profile.id),
        user_id=current_user.id,
        request=request
    )

    return profile


@router.put("/me/profile/doctor", response_model=DoctorProfileOut)
def update_doctor_profile(
    profile_in: DoctorProfileUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.DOCTOR]))
):
    """
    Doctor Endpoint: Update own professional profile info.
    """
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile record missing."
        )

    update_data = profile_in.model_dump(exclude_unset=True)
    if "department_id" in update_data and update_data["department_id"]:
        dept = db.query(Department).filter(Department.id == update_data["department_id"]).first()
        if not dept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found."
            )

    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    log_action(
        db=db,
        action="PROFILE_UPDATE_DOCTOR",
        resource="doctor_profiles",
        resource_id=str(profile.id),
        user_id=current_user.id,
        request=request
    )

    return profile


@router.get("/doctors", response_model=List[UserOut])
def list_doctors(
    department_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """
    Public Endpoint: Get list of active doctors, optionally filtered by department.
    """
    query = db.query(User).join(DoctorProfile).filter(User.role == UserRole.DOCTOR, User.is_active == True)
    if department_id:
        query = query.filter(DoctorProfile.department_id == department_id)
    
    return query.order_by(User.full_name.asc()).all()


@router.get("/", response_model=List[UserOut])
def list_users(
    role: Optional[UserRole] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Admin Endpoint: List all platform users with optional role filter.
    """
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    
    return query.order_by(User.created_at.desc()).all()
