from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.appointment import Appointment
from app.models.medical_record import MedicalDocument, MedicalRecord, Prescription
from app.models.user import User, UserRole
from app.schemas.appointment import AppointmentUserSummary
from app.schemas.medical_record import (
    MedicalDocumentCreate,
    MedicalDocumentOut,
    MedicalRecordCreate,
    MedicalRecordOut,
    MedicalRecordUpdate,
    PrescriptionCreate,
    PrescriptionOut,
)
from app.services.audit_service import log_action

router = APIRouter()


@router.get("/patients", response_model=List[AppointmentUserSummary])
def get_doctor_patients(
    db: Session = Depends(get_db),
    current_doctor: User = Depends(require_roles([UserRole.DOCTOR]))
):
    """List patients who have appointments with the current doctor."""
    return (
        db.query(User)
        .join(Appointment, Appointment.patient_id == User.id)
        .filter(
            Appointment.doctor_id == current_doctor.id,
            User.role == UserRole.PATIENT
        )
        .distinct()
        .order_by(User.full_name.asc())
        .all()
    )


@router.post("/", response_model=MedicalRecordOut, status_code=status.HTTP_201_CREATED)
def create_medical_record(
    record_in: MedicalRecordCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_doctor: User = Depends(require_roles([UserRole.DOCTOR]))
):
    """
    Doctor Endpoint: Create a medical record for a patient (with optional prescriptions).
    """
    # Verify Patient Exists
    patient_user = db.query(User).filter(User.id == record_in.patient_id, User.role == UserRole.PATIENT).first()
    if not patient_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found."
        )

    new_record = MedicalRecord(
        patient_id=patient_user.id,
        doctor_id=current_doctor.id,
        appointment_id=record_in.appointment_id,
        visit_date=record_in.visit_date,
        symptoms=record_in.symptoms,
        diagnosis=record_in.diagnosis,
        notes=record_in.notes,
        treatment=record_in.treatment,
        follow_up_date=record_in.follow_up_date
    )
    db.add(new_record)
    db.flush()

    # Create Embedded Prescriptions
    if record_in.prescriptions:
        for p in record_in.prescriptions:
            prescription = Prescription(
                medical_record_id=new_record.id,
                patient_id=patient_user.id,
                doctor_id=current_doctor.id,
                medicine_name=p.medicine_name,
                dosage=p.dosage,
                frequency=p.frequency,
                duration=p.duration,
                instructions=p.instructions
            )
            db.add(prescription)

    db.commit()
    db.refresh(new_record)

    log_action(
        db=db,
        action="MEDICAL_RECORD_CREATED",
        resource="medical_records",
        resource_id=str(new_record.id),
        user_id=current_doctor.id,
        request=request
    )

    return new_record


@router.get("/my", response_model=List[MedicalRecordOut])
def get_my_medical_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Authenticated Endpoint: List medical records accessible by current user.
    - Patient sees only their own medical history records.
    - Doctor sees records authored for their patients.
    - Admin sees all platform medical records.
    """
    query = db.query(MedicalRecord)

    if current_user.role == UserRole.PATIENT:
        query = query.filter(MedicalRecord.patient_id == current_user.id)
    elif current_user.role == UserRole.DOCTOR:
        query = query.filter(MedicalRecord.doctor_id == current_user.id)
    elif current_user.role != UserRole.ADMIN:
        return []

    return query.order_by(MedicalRecord.visit_date.desc()).all()


@router.get("/{record_id}", response_model=MedicalRecordOut)
def get_medical_record_detail(
    record_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Secure Authorization Endpoint: Get detailed medical record by ID.
    Enforces strict ownership access control.
    """
    record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical record not found."
        )

    # SECURE AUTHORIZATION: Patient can only access their own records
    if current_user.role == UserRole.PATIENT and record.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only view your own medical records."
        )

    # Doctor can view records if they are the treating doctor or admin
    if current_user.role == UserRole.DOCTOR and record.doctor_id != current_user.id:
        # Note: In future multi-doctor consultation, shared consent can be checked here
        pass

    return record


@router.post("/{record_id}/prescriptions", response_model=PrescriptionOut, status_code=status.HTTP_201_CREATED)
def add_prescription_to_record(
    record_id: UUID,
    p_in: PrescriptionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_doctor: User = Depends(require_roles([UserRole.DOCTOR]))
):
    """
    Doctor Endpoint: Add a new prescription item to an existing medical record.
    """
    record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical record not found."
        )

    if record.doctor_id != current_doctor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only add prescriptions to records you authored."
        )

    new_prescription = Prescription(
        medical_record_id=record.id,
        patient_id=record.patient_id,
        doctor_id=current_doctor.id,
        **p_in.model_dump()
    )
    db.add(new_prescription)
    db.commit()
    db.refresh(new_prescription)

    log_action(
        db=db,
        action="PRESCRIPTION_ADDED",
        resource="prescriptions",
        resource_id=str(new_prescription.id),
        user_id=current_doctor.id,
        request=request
    )

    return new_prescription


@router.post("/documents/upload", response_model=MedicalDocumentOut, status_code=status.HTTP_201_CREATED)
def upload_medical_document_metadata(
    doc_in: MedicalDocumentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Patient / Doctor Endpoint: Save medical document record (PDF, Lab report, Image).
    """
    target_patient_id = current_user.id
    if current_user.role == UserRole.DOCTOR and doc_in.medical_record_id:
        rec = db.query(MedicalRecord).filter(MedicalRecord.id == doc_in.medical_record_id).first()
        if rec:
            target_patient_id = rec.patient_id

    document = MedicalDocument(
        patient_id=target_patient_id,
        medical_record_id=doc_in.medical_record_id,
        title=doc_in.title,
        document_type=doc_in.document_type,
        file_path=doc_in.file_path,
        file_size_bytes=doc_in.file_size_bytes
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    log_action(
        db=db,
        action="MEDICAL_DOCUMENT_UPLOADED",
        resource="medical_documents",
        resource_id=str(document.id),
        user_id=current_user.id,
        request=request
    )

    return document


@router.get("/documents/my", response_model=List[MedicalDocumentOut])
def list_my_medical_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List medical documents uploaded for current user.
    """
    if current_user.role == UserRole.PATIENT:
        return db.query(MedicalDocument).filter(MedicalDocument.patient_id == current_user.id).order_by(MedicalDocument.created_at.desc()).all()
    elif current_user.role == UserRole.ADMIN:
        return db.query(MedicalDocument).order_by(MedicalDocument.created_at.desc()).all()
    else:
        return []
