from datetime import datetime, timedelta, timezone
import hashlib
import logging
import secrets
import smtplib
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.department import Department
from app.models.profile import DoctorProfile, PatientProfile
from app.models.password_reset import PasswordResetToken
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, RefreshTokenRequest, Token
from app.schemas.password_reset import PasswordResetConfirm, PasswordResetRequest
from app.schemas.user import DoctorRegisterRequest, PatientRegisterRequest, UserOut
from app.services.audit_service import log_action
from app.services.password_reset_service import password_reset_email_configured, send_password_reset_email

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register/patient", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_patient(
    patient_in: PatientRegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new Patient account.
    Creates both User record and associated PatientProfile record.
    """
    # Check if user email already exists
    existing_user = db.query(User).filter(User.email == patient_in.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # Hash password
    hashed_password = get_password_hash(patient_in.password)

    # Create User
    new_user = User(
        full_name=patient_in.full_name,
        email=patient_in.email.lower(),
        phone=patient_in.phone,
        password_hash=hashed_password,
        role=UserRole.PATIENT,
        is_active=True,
        is_verified=False
    )
    db.add(new_user)
    db.flush()  # Generate user id before creating profile

    # Create Patient Profile
    profile_data = patient_in.profile.model_dump() if patient_in.profile else {}
    patient_profile = PatientProfile(
        user_id=new_user.id,
        **profile_data
    )
    db.add(patient_profile)
    db.commit()
    db.refresh(new_user)

    # Log audit event
    log_action(
        db=db,
        action="PATIENT_REGISTER",
        resource="users",
        resource_id=str(new_user.id),
        user_id=new_user.id,
        request=request
    )

    return new_user


@router.post("/register/doctor", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_doctor(
    doctor_in: DoctorRegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new Doctor account.
    Creates User record and DoctorProfile record after verifying license uniqueness.
    """
    # Check email uniqueness
    existing_user = db.query(User).filter(User.email == doctor_in.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # Check license number uniqueness
    existing_license = db.query(DoctorProfile).filter(
        DoctorProfile.license_number == doctor_in.profile.license_number
    ).first()
    if existing_license:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A doctor with this license number already exists."
        )

    # Verify department ID if provided
    if doctor_in.profile.department_id:
        department = db.query(Department).filter(Department.id == doctor_in.profile.department_id).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found."
            )

    # Hash password
    hashed_password = get_password_hash(doctor_in.password)

    # Create User
    new_user = User(
        full_name=doctor_in.full_name,
        email=doctor_in.email.lower(),
        phone=doctor_in.phone,
        password_hash=hashed_password,
        role=UserRole.DOCTOR,
        is_active=True,
        is_verified=False
    )
    db.add(new_user)
    db.flush()

    # Create Doctor Profile
    doctor_profile = DoctorProfile(
        user_id=new_user.id,
        **doctor_in.profile.model_dump()
    )
    db.add(doctor_profile)
    db.commit()
    db.refresh(new_user)

    # Log audit event
    log_action(
        db=db,
        action="DOCTOR_REGISTER",
        resource="users",
        resource_id=str(new_user.id),
        user_id=new_user.id,
        request=request
    )

    return new_user


@router.post("/login", response_model=Token)
def login(
    login_in: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user credentials, update last login timestamp, and issue JWT tokens.
    """
    user = db.query(User).filter(User.email == login_in.email.lower()).first()
    if not user or not verify_password(login_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support."
        )

    # Update last login timestamp
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    # Generate JWT Tokens
    access_token = create_access_token(subject=str(user.id), role=user.role.value)
    refresh_token = create_refresh_token(subject=str(user.id), role=user.role.value)

    # Log audit event
    log_action(
        db=db,
        action="USER_LOGIN",
        resource="users",
        resource_id=str(user.id),
        user_id=user.id,
        request=request
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user_id=str(user.id),
        role=user.role.value,
        full_name=user.full_name
    )


@router.post("/password/forgot", status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(
    reset_in: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    if not password_reset_email_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password reset email is not configured. Contact the system administrator."
        )

    generic_response = {
        "message": "If an active patient or doctor account exists for that email, a password reset link will be sent."
    }
    user = db.query(User).filter(
        User.email == reset_in.email.lower(),
        User.role.in_([UserRole.PATIENT, UserRole.DOCTOR]),
        User.is_active.is_(True)
    ).first()
    if not user:
        return generic_response

    now = datetime.now(timezone.utc)
    recent_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.created_at >= now - timedelta(minutes=1)
    ).first()
    if recent_token:
        return generic_response

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None)
    ).update({PasswordResetToken.used_at: now}, synchronize_session=False)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=now + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_MINUTES)
    )
    db.add(reset_token)
    db.commit()

    reset_url = (
        f"{settings.frontend_url}/"
        f"#reset-password/{raw_token}"
    )
    try:
        send_password_reset_email(user.email, reset_url)
    except (OSError, smtplib.SMTPException):
        reset_token.used_at = datetime.now(timezone.utc)
        db.commit()
        logger.exception("Unable to deliver password reset email.")

    return generic_response


@router.post("/password/reset")
def reset_password(
    reset_in: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    token_hash = hashlib.sha256(reset_in.token.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used_at.is_(None),
        PasswordResetToken.expires_at > now
    ).first()
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid or expired. Request a new link."
        )

    user = db.query(User).filter(
        User.id == reset_token.user_id,
        User.role.in_([UserRole.PATIENT, UserRole.DOCTOR]),
        User.is_active.is_(True)
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid or expired. Request a new link."
        )

    claimed = db.query(PasswordResetToken).filter(
        PasswordResetToken.id == reset_token.id,
        PasswordResetToken.used_at.is_(None),
        PasswordResetToken.expires_at > now
    ).update({PasswordResetToken.used_at: now}, synchronize_session=False)
    if claimed != 1:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid or expired. Request a new link."
        )

    user.password_hash = get_password_hash(reset_in.new_password)
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None)
    ).update({PasswordResetToken.used_at: now}, synchronize_session=False)
    db.commit()
    return {"message": "Password reset successfully. You can now sign in with your new password."}


@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_in: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Obtain a new Access Token using a valid Refresh Token.
    """
    payload = decode_token(refresh_in.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token."
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive."
        )

    new_access_token = create_access_token(subject=str(user.id), role=user.role.value)
    new_refresh_token = create_refresh_token(subject=str(user.id), role=user.role.value)

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        user_id=str(user.id),
        role=user.role.value,
        full_name=user.full_name
    )


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Retrieve current authenticated user details along with profile data.
    """
    return current_user
