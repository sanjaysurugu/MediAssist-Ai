from pathlib import Path
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.department import Department
from app.models.profile import DoctorProfile
from app.models.user import User, UserAvatar, UserRole
from app.schemas.profile import DoctorAvailabilityUpdate, DoctorProfileOut, DoctorProfileUpdate
from app.schemas.user import DoctorPublicOut
from app.services.audit_service import log_action

router = APIRouter()
AVATAR_DIRECTORY = Path(__file__).resolve().parents[4] / "uploads" / "avatars"


@router.get("/", response_model=List[DoctorPublicOut])
def search_doctors(
    department_id: Optional[UUID] = Query(None, description="Filter by Department ID"),
    specialization: Optional[str] = Query(None, description="Filter by Specialization"),
    query: Optional[str] = Query(None, description="Search doctor name or bio"),
    min_experience: Optional[int] = Query(None, ge=0, description="Minimum years of experience"),
    max_fee: Optional[float] = Query(None, ge=0.0, description="Maximum consultation fee"),
    available_only: bool = Query(False, description="Filter available doctors only"),
    db: Session = Depends(get_db)
):
    """
    Public & Patient Endpoint: Search doctors with multi-criteria filtering.
    """
    sql_query = db.query(User).join(DoctorProfile).filter(
        User.role == UserRole.DOCTOR,
        User.is_active == True
    )

    if department_id:
        sql_query = sql_query.filter(DoctorProfile.department_id == department_id)

    if specialization:
        sql_query = sql_query.filter(DoctorProfile.specialization.ilike(f"%{specialization}%"))

    if query:
        search_pattern = f"%{query}%"
        sql_query = sql_query.filter(
            (User.full_name.ilike(search_pattern)) | (DoctorProfile.bio.ilike(search_pattern))
        )

    if min_experience is not None:
        sql_query = sql_query.filter(DoctorProfile.experience_years >= min_experience)

    if max_fee is not None:
        sql_query = sql_query.filter(DoctorProfile.consultation_fee <= max_fee)

    if available_only:
        sql_query = sql_query.filter(DoctorProfile.available == True)

    users = sql_query.order_by(User.full_name.asc()).all()

    # Map to DoctorPublicOut
    results = []
    for u in users:
        doc = u.doctor_profile
        results.append(DoctorPublicOut(
            id=doc.id,
            user_id=u.id,
            full_name=u.full_name,
            email=u.email,
            phone=u.phone,
            avatar_url=f"/doctors/{doc.id}/avatar" if u.avatar_url else None,
            specialization=doc.specialization,
            license_number=doc.license_number,
            experience_years=doc.experience_years,
            qualification=doc.qualification,
            consultation_fee=doc.consultation_fee,
            bio=doc.bio,
            available=doc.available,
            is_verified=u.is_verified,
            department=doc.department
        ))
    return results


@router.get("/{doctor_id}/avatar")
def get_doctor_avatar(doctor_id: UUID, db: Session = Depends(get_db)):
    doctor = db.query(DoctorProfile).filter(
        (DoctorProfile.id == doctor_id) | (DoctorProfile.user_id == doctor_id)
    ).first()
    if (
        not doctor
        or not doctor.user
        or doctor.user.role != UserRole.DOCTOR
        or not doctor.user.is_active
        or not doctor.user.avatar_url
        or Path(doctor.user.avatar_url).name != doctor.user.avatar_url
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor photo not found.")

    avatar = db.query(UserAvatar).filter(UserAvatar.user_id == doctor.user_id).first()
    if avatar:
        return Response(
            content=avatar.image_data,
            media_type=avatar.content_type,
            headers={"Cache-Control": "public, max-age=300"}
        )

    avatar_path = AVATAR_DIRECTORY / doctor.user.avatar_url
    if not avatar_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor photo not found.")
    media_type = {
        ".jpg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(avatar_path.suffix.lower())
    if not media_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor photo not found.")

    return FileResponse(
        avatar_path,
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=300"}
    )


@router.get("/{doctor_id}", response_model=DoctorPublicOut)
def get_doctor_by_id(doctor_id: UUID, db: Session = Depends(get_db)):
    """
    Public Endpoint: View doctor detail page by Doctor Profile ID or User ID.
    """
    # Check if doctor_id matches doctor_profile.id or user.id
    doc = db.query(DoctorProfile).filter(
        (DoctorProfile.id == doctor_id) | (DoctorProfile.user_id == doctor_id)
    ).first()

    if not doc or not doc.user or doc.user.role != UserRole.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found."
        )

    u = doc.user
    return DoctorPublicOut(
        id=doc.id,
        user_id=u.id,
        full_name=u.full_name,
        email=u.email,
        phone=u.phone,
        avatar_url=f"/doctors/{doc.id}/avatar" if u.avatar_url else None,
        specialization=doc.specialization,
        license_number=doc.license_number,
        experience_years=doc.experience_years,
        qualification=doc.qualification,
        consultation_fee=doc.consultation_fee,
        bio=doc.bio,
        available=doc.available,
        is_verified=u.is_verified,
        department=doc.department
    )


@router.patch("/me/availability", response_model=DoctorProfileOut)
def toggle_availability(
    avail_in: DoctorAvailabilityUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_doctor: User = Depends(require_roles([UserRole.DOCTOR]))
):
    """
    Doctor Endpoint: Toggle doctor availability status (available for appointments).
    """
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == current_doctor.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile missing."
        )

    profile.available = avail_in.available
    db.commit()
    db.refresh(profile)

    log_action(
        db=db,
        action="DOCTOR_TOGGLE_AVAILABILITY",
        resource="doctor_profiles",
        resource_id=str(profile.id),
        user_id=current_doctor.id,
        request=request
    )

    return profile


@router.get("/me/dashboard")
def doctor_dashboard(
    db: Session = Depends(get_db),
    current_doctor: User = Depends(require_roles([UserRole.DOCTOR]))
):
    """
    Doctor Dashboard Endpoint: Summary information for logged in doctor.
    """
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == current_doctor.id).first()
    return {
        "doctor_id": str(profile.id) if profile else None,
        "full_name": current_doctor.full_name,
        "email": current_doctor.email,
        "specialization": profile.specialization if profile else None,
        "available": profile.available if profile else False,
        "is_verified": current_doctor.is_verified,
        "account_status": "Active" if current_doctor.is_active else "Inactive",
        "consultation_fee": profile.consultation_fee if profile else 0.0,
    }
