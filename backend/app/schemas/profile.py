from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


# Patient Profile Schemas
class PatientProfileBase(BaseModel):
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    blood_group: Optional[str] = Field(None, max_length=10)
    emergency_contact: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None


class PatientProfileCreate(PatientProfileBase):
    pass


class PatientProfileUpdate(PatientProfileBase):
    pass


class PatientProfileOut(PatientProfileBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Doctor Profile Schemas
class DoctorProfileBase(BaseModel):
    specialization: str = Field(..., max_length=255)
    license_number: str = Field(..., max_length=100)
    experience_years: int = Field(0, ge=0)
    qualification: Optional[str] = Field(None, max_length=255)
    consultation_fee: float = Field(0.0, ge=0.0)
    bio: Optional[str] = None
    available: bool = True
    department_id: Optional[UUID] = None


class DoctorProfileCreate(DoctorProfileBase):
    pass


class DoctorProfileUpdate(BaseModel):
    specialization: Optional[str] = Field(None, max_length=255)
    experience_years: Optional[int] = Field(None, ge=0)
    qualification: Optional[str] = Field(None, max_length=255)
    consultation_fee: Optional[float] = Field(None, ge=0.0)
    bio: Optional[str] = None
    available: Optional[bool] = None
    department_id: Optional[UUID] = None


class DoctorAvailabilityUpdate(BaseModel):
    available: bool


class DoctorProfileOut(DoctorProfileBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
