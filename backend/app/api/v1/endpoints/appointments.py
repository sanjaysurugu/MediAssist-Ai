from datetime import date, datetime, time, timedelta
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.appointment import Appointment, AppointmentStatus
from app.models.profile import DoctorProfile
from app.models.user import User, UserRole
from app.schemas.appointment import AppointmentCreate, AppointmentOut, AppointmentUpdateStatus, TimeSlot
from app.services.audit_service import log_action

router = APIRouter()


@router.post("/", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def book_appointment(
    apt_in: AppointmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.PATIENT]))
):
    """
    Patient Endpoint: Book a new appointment with a doctor.
    Prevents double booking at database & application layers.
    """
    # 1. Validate Appointment Date is not in the past
    if apt_in.appointment_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot book an appointment for a past date."
        )

    # 2. Validate Doctor Exists & Is Active
    # Accept doctor_id as either User ID or Doctor Profile ID
    doctor_user = db.query(User).filter(User.id == apt_in.doctor_id, User.role == UserRole.DOCTOR).first()
    if not doctor_user:
        doc_prof = db.query(DoctorProfile).filter(DoctorProfile.id == apt_in.doctor_id).first()
        if doc_prof and doc_prof.user:
            doctor_user = doc_prof.user
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor not found."
            )

    if not doctor_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected doctor account is currently inactive."
        )

    # 3. Check Doctor Availability Profile Flag
    if doctor_user.doctor_profile and not doctor_user.doctor_profile.available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor is currently unavailable for bookings."
        )

    # 4. Check for Double Booking in Application Layer
    existing_apt = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_user.id,
        Appointment.appointment_date == apt_in.appointment_date,
        Appointment.start_time == apt_in.start_time,
        Appointment.status.notin_([AppointmentStatus.CANCELLED, AppointmentStatus.REJECTED])
    ).first()

    if existing_apt:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This time slot is already booked for the selected doctor."
        )

    # 5. Create Appointment Record
    new_appointment = Appointment(
        patient_id=current_user.id,
        doctor_id=doctor_user.id,
        appointment_date=apt_in.appointment_date,
        start_time=apt_in.start_time,
        end_time=apt_in.end_time,
        reason=apt_in.reason,
        status=AppointmentStatus.PENDING
    )

    try:
        db.add(new_appointment)
        db.commit()
        db.refresh(new_appointment)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Double booking detected: Time slot already reserved."
        )

    log_action(
        db=db,
        action="APPOINTMENT_BOOKED",
        resource="appointments",
        resource_id=str(new_appointment.id),
        user_id=current_user.id,
        request=request
    )

    return new_appointment


@router.get("/my", response_model=List[AppointmentOut])
def get_my_appointments(
    status_filter: Optional[AppointmentStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Authenticated Endpoint: Get appointments for the current logged-in user.
    Returns patient appointments if patient, or doctor appointments if doctor.
    """
    query = db.query(Appointment)

    if current_user.role == UserRole.PATIENT:
        query = query.filter(Appointment.patient_id == current_user.id)
    elif current_user.role == UserRole.DOCTOR:
        query = query.filter(Appointment.doctor_id == current_user.id)
    elif current_user.role != UserRole.ADMIN:
        return []

    if status_filter:
        query = query.filter(Appointment.status == status_filter)

    return query.order_by(Appointment.appointment_date.desc(), Appointment.start_time.asc()).all()


@router.get("/doctor/today", response_model=List[AppointmentOut])
def get_doctor_today_schedule(
    db: Session = Depends(get_db),
    current_doctor: User = Depends(require_roles([UserRole.DOCTOR]))
):
    """
    Doctor Endpoint: View doctor's scheduled appointments for today.
    """
    today = date.today()
    return db.query(Appointment).filter(
        Appointment.doctor_id == current_doctor.id,
        Appointment.appointment_date == today
    ).order_by(Appointment.start_time.asc()).all()


@router.get("/available-slots", response_model=List[TimeSlot])
def get_available_time_slots(
    doctor_id: UUID,
    slot_date: date = Query(..., alias="date"),
    db: Session = Depends(get_db)
):
    """
    Public / Patient Endpoint: Generate available 30-minute time slots for a doctor on a given date.
    """
    # Verify Doctor
    doctor_user = db.query(User).filter(User.id == doctor_id, User.role == UserRole.DOCTOR).first()
    if not doctor_user:
        doc_prof = db.query(DoctorProfile).filter(DoctorProfile.id == doctor_id).first()
        if doc_prof and doc_prof.user:
            doctor_user = doc_prof.user

    if not doctor_user or not doctor_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found or inactive."
        )

    # Get booked start times for this doctor on slot_date
    booked_apts = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_user.id,
        Appointment.appointment_date == slot_date,
        Appointment.status.notin_([AppointmentStatus.CANCELLED, AppointmentStatus.REJECTED])
    ).all()

    booked_start_times = {apt.start_time for apt in booked_apts}

    # Generate standard slots between 09:00 AM and 05:00 PM (30 min slots)
    slots = []
    curr_dt = datetime.combine(slot_date, time(9, 0))
    end_dt = datetime.combine(slot_date, time(17, 0))

    while curr_dt < end_dt:
        st_time = curr_dt.time()
        end_time_dt = curr_dt + timedelta(minutes=30)
        en_time = end_time_dt.time()

        is_avail = st_time not in booked_start_times
        slots.append(TimeSlot(start_time=st_time, end_time=en_time, is_available=is_avail))

        curr_dt = end_time_dt

    return slots


@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment_detail(
    appointment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get appointment details by ID (Patient, Doctor, or Admin).
    """
    apt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not apt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found."
        )

    # Authorization check
    if current_user.role == UserRole.PATIENT and apt.patient_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    if current_user.role == UserRole.DOCTOR and apt.doctor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return apt


@router.patch("/{appointment_id}/status", response_model=AppointmentOut)
def update_appointment_status(
    appointment_id: UUID,
    status_in: AppointmentUpdateStatus,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update appointment status:
    - Doctor can set status to CONFIRMED, REJECTED, or COMPLETED.
    - Patient can set status to CANCELLED for pending/confirmed appointments.
    """
    apt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not apt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found."
        )

    target_status = status_in.status

    # Role Permissions Validation
    if current_user.role == UserRole.PATIENT:
        if apt.patient_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        if target_status != AppointmentStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patients can only cancel their appointments."
            )
        if apt.status in [AppointmentStatus.COMPLETED, AppointmentStatus.REJECTED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel appointment with status {apt.status.value}."
            )

    elif current_user.role == UserRole.DOCTOR:
        if apt.doctor_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        if target_status not in [AppointmentStatus.CONFIRMED, AppointmentStatus.REJECTED, AppointmentStatus.COMPLETED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Doctor can only set status to confirmed, rejected, or completed."
            )

    apt.status = target_status
    if status_in.notes:
        apt.notes = status_in.notes

    db.commit()
    db.refresh(apt)

    log_action(
        db=db,
        action=f"APPOINTMENT_STATUS_{target_status.value.upper()}",
        resource="appointments",
        resource_id=str(apt.id),
        user_id=current_user.id,
        request=request
    )

    return apt
