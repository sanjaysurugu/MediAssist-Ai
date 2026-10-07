from datetime import date, datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.appointment import AppointmentUserSummary


# Prescription Schemas
class PrescriptionBase(BaseModel):
    medicine_name: str = Field(..., min_length=1, max_length=255)
    dosage: str = Field(..., min_length=1, max_length=100)
    frequency: str = Field(..., min_length=1, max_length=100)
    duration: str = Field(..., min_length=1, max_length=100)
    instructions: Optional[str] = None


class PrescriptionCreate(PrescriptionBase):
    pass


class PrescriptionOut(PrescriptionBase):
    id: UUID
    medical_record_id: UUID
    patient_id: UUID
    doctor_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Medical Document Schemas
class MedicalDocumentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    document_type: str = Field(..., max_length=50, description="PDF, Image, Lab Report, etc.")
    file_path: str = Field(..., max_length=512)
    file_size_bytes: int = Field(0, ge=0)


class MedicalDocumentCreate(MedicalDocumentBase):
    medical_record_id: Optional[UUID] = None


class MedicalDocumentOut(MedicalDocumentBase):
    id: UUID
    patient_id: UUID
    medical_record_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Medical Record Schemas
class MedicalRecordBase(BaseModel):
    patient_id: UUID
    appointment_id: Optional[UUID] = None
    visit_date: date
    symptoms: str = Field(..., min_length=3)
    diagnosis: str = Field(..., min_length=3)
    notes: Optional[str] = None
    treatment: str = Field(..., min_length=3)
    follow_up_date: Optional[date] = None


class MedicalRecordCreate(MedicalRecordBase):
    prescriptions: Optional[List[PrescriptionCreate]] = []


class MedicalRecordUpdate(BaseModel):
    symptoms: Optional[str] = None
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    treatment: Optional[str] = None
    follow_up_date: Optional[date] = None


class MedicalRecordOut(MedicalRecordBase):
    id: UUID
    doctor_id: UUID
    created_at: datetime
    updated_at: datetime
    patient: Optional[AppointmentUserSummary] = None
    doctor: Optional[AppointmentUserSummary] = None
    prescriptions: List[PrescriptionOut] = []
    documents: List[MedicalDocumentOut] = []

    model_config = ConfigDict(from_attributes=True)
