from datetime import date, datetime, time
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.models.appointment import AppointmentStatus


class AppointmentBase(BaseModel):
    doctor_id: UUID
    appointment_date: date
    start_time: time
    end_time: time
    reason: str = Field(..., min_length=3, description="Reason for booking appointment")


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdateStatus(BaseModel):
    status: AppointmentStatus
    notes: Optional[str] = None


class AppointmentUserSummary(BaseModel):
    id: UUID
    full_name: str
    email: str
    phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AppointmentOut(BaseModel):
    id: UUID
    patient_id: UUID
    doctor_id: UUID
    appointment_date: date
    start_time: time
    end_time: time
    reason: str
    status: AppointmentStatus
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    patient: Optional[AppointmentUserSummary] = None
    doctor: Optional[AppointmentUserSummary] = None

    model_config = ConfigDict(from_attributes=True)


class TimeSlot(BaseModel):
    start_time: time
    end_time: time
    is_available: bool
