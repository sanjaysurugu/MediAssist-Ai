from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.user import UserRole
from app.schemas.department import DepartmentOut
from app.schemas.profile import PatientProfileOut, PatientProfileCreate, DoctorProfileOut, DoctorProfileCreate


# Base User Schema
class UserBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)


# Registration Schemas
class PatientRegisterRequest(UserBase):
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    profile: Optional[PatientProfileCreate] = None


class DoctorRegisterRequest(UserBase):
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    profile: DoctorProfileCreate


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)


# Admin Actions Schemas
class UserStatusUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class AdminDashboardTrendPoint(BaseModel):
    date: datetime
    patient_registrations: int
    appointments: int


class AdminDashboardStats(BaseModel):
    total_users: int
    total_patients: int
    total_doctors: int
    total_departments: int
    active_users: int
    unverified_doctors: int
    patient_registrations_today: int
    appointments_today: int
    daily_trends: List[AdminDashboardTrendPoint]


# User Response Schemas
class UserOut(UserBase):
    id: UUID
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    avatar_url: Optional[str] = None
    patient_profile: Optional[PatientProfileOut] = None
    doctor_profile: Optional[DoctorProfileOut] = None

    model_config = ConfigDict(from_attributes=True)


# Doctor Public Card View
class DoctorPublicOut(BaseModel):
    id: UUID
    user_id: UUID
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    specialization: str
    license_number: str
    experience_years: int
    qualification: Optional[str] = None
    consultation_fee: float
    bio: Optional[str] = None
    available: bool
    is_verified: bool
    department: Optional[DepartmentOut] = None

    model_config = ConfigDict(from_attributes=True)
