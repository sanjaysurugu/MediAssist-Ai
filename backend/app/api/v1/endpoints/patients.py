from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.profile import PatientProfile
from app.models.user import User, UserRole
from app.schemas.profile import PatientProfileOut, PatientProfileUpdate
from app.schemas.user import UserOut
from app.services.audit_service import log_action

router = APIRouter()


@router.get("/me", response_model=UserOut)
def get_patient_profile(
    current_patient: User = Depends(require_roles([UserRole.PATIENT]))
):
    """
    Patient Endpoint: Get logged-in patient user details and medical profile.
    """
    return current_patient


@router.put("/me", response_model=PatientProfileOut)
def update_patient_profile(
    profile_in: PatientProfileUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_patient: User = Depends(require_roles([UserRole.PATIENT]))
):
    """
    Patient Endpoint: Update logged-in patient medical profile.
    """
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == current_patient.id).first()
    if not profile:
        profile = PatientProfile(user_id=current_patient.id)
        db.add(profile)
        db.flush()

    update_data = profile_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    log_action(
        db=db,
        action="PATIENT_PROFILE_UPDATE",
        resource="patient_profiles",
        resource_id=str(profile.id),
        user_id=current_patient.id,
        request=request
    )

    return profile
