from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.appointment import Appointment
from app.models.department import Department
from app.models.profile import DoctorProfile
from app.models.user import User, UserRole
from app.schemas.user import AdminDashboardStats, AdminDashboardTrendPoint, UserOut, UserStatusUpdate
from app.services.audit_service import log_action

router = APIRouter()


@router.get("/stats", response_model=AdminDashboardStats)
def get_admin_dashboard_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Admin Endpoint: Aggregate real-time statistics for the admin dashboard.
    """
    total_users = db.query(User).count()
    total_patients = db.query(User).filter(User.role == UserRole.PATIENT).count()
    total_doctors = db.query(User).filter(User.role == UserRole.DOCTOR).count()
    total_departments = db.query(Department).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    unverified_doctors = db.query(User).filter(
        User.role == UserRole.DOCTOR,
        User.is_verified == False
    ).count()

    today = date.today()
    local_timezone = datetime.now().astimezone().tzinfo
    today_start = datetime.combine(today, time.min, tzinfo=local_timezone).astimezone(timezone.utc)
    tomorrow_start = datetime.combine(
        today + timedelta(days=1),
        time.min,
        tzinfo=local_timezone
    ).astimezone(timezone.utc)
    patient_registrations_today = db.query(User).filter(
        User.role == UserRole.PATIENT,
        User.created_at >= today_start,
        User.created_at < tomorrow_start
    ).count()
    appointments_today = db.query(Appointment).filter(
        Appointment.appointment_date == today
    ).count()

    trend_start = today - timedelta(days=13)
    trend_end = today + timedelta(days=1)
    local_midnight = datetime.combine(trend_start, time.min, tzinfo=local_timezone)
    trend_start_utc = local_midnight.astimezone(timezone.utc)
    trend_end_utc = datetime.combine(
        trend_end,
        time.min,
        tzinfo=local_timezone
    ).astimezone(timezone.utc)
    patient_counts = {trend_start + timedelta(days=offset): 0 for offset in range(14)}
    appointment_counts = {day: 0 for day in patient_counts}

    patient_dates = db.query(User.created_at).filter(
        User.role == UserRole.PATIENT,
        User.created_at >= trend_start_utc,
        User.created_at < trend_end_utc
    ).all()
    for (created_at,) in patient_dates:
        created_at = created_at.replace(tzinfo=timezone.utc) if created_at.tzinfo is None else created_at
        local_date = created_at.astimezone(local_timezone).date()
        if local_date in patient_counts:
            patient_counts[local_date] += 1

    appointment_dates = db.query(Appointment.appointment_date).filter(
        Appointment.appointment_date >= trend_start,
        Appointment.appointment_date < trend_end
    ).all()
    for (appointment_date,) in appointment_dates:
        appointment_counts[appointment_date] += 1

    return AdminDashboardStats(
        total_users=total_users,
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_departments=total_departments,
        active_users=active_users,
        unverified_doctors=unverified_doctors,
        patient_registrations_today=patient_registrations_today,
        appointments_today=appointments_today,
        daily_trends=[
            AdminDashboardTrendPoint(
                date=datetime.combine(day, time.min),
                patient_registrations=patient_counts[day],
                appointments=appointment_counts[day]
            )
            for day in patient_counts
        ]
    )


@router.get("/users", response_model=List[UserOut])
def list_users_admin(
    role: Optional[UserRole] = Query(None, description="Filter by user role"),
    is_active: Optional[bool] = Query(None, description="Filter active/inactive accounts"),
    is_verified: Optional[bool] = Query(None, description="Filter verified/unverified accounts"),
    search: Optional[str] = Query(None, description="Search by full name or email"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Admin Endpoint: Search and filter all registered users on the platform.
    """
    query = db.query(User)

    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if is_verified is not None:
        query = query.filter(User.is_verified == is_verified)
    if search:
        pattern = f"%{search}%"
        query = query.filter((User.full_name.ilike(pattern)) | (User.email.ilike(pattern)))

    return query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()


@router.patch("/users/{user_id}/status", response_model=UserOut)
def update_user_status(
    user_id: UUID,
    status_in: UserStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Admin Endpoint: Activate/Deactivate user accounts or change verification status.
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    if status_in.is_active is not None:
        target_user.is_active = status_in.is_active
    if status_in.is_verified is not None:
        target_user.is_verified = status_in.is_verified

    db.commit()
    db.refresh(target_user)

    log_action(
        db=db,
        action="ADMIN_UPDATE_USER_STATUS",
        resource="users",
        resource_id=str(target_user.id),
        user_id=admin_user.id,
        request=request
    )

    return target_user


@router.patch("/doctors/{doctor_id}/verify", response_model=UserOut)
def verify_doctor_license(
    doctor_id: UUID,
    verify: bool = Query(True, description="Set True to verify, False to revoke verification"),
    request: Request = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Admin Endpoint: Verify or revoke doctor credentials after reviewing medical license.
    """
    doc_profile = db.query(DoctorProfile).filter(
        (DoctorProfile.id == doctor_id) | (DoctorProfile.user_id == doctor_id)
    ).first()

    if not doc_profile or not doc_profile.user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found."
        )

    doctor_user = doc_profile.user
    doctor_user.is_verified = verify
    db.commit()
    db.refresh(doctor_user)

    log_action(
        db=db,
        action="ADMIN_VERIFY_DOCTOR",
        resource="users",
        resource_id=str(doctor_user.id),
        user_id=admin_user.id,
        request=request
    )

    return doctor_user
