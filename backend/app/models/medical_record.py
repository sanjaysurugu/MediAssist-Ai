import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True, index=True)
    visit_date = Column(Date, nullable=False, index=True)
    symptoms = Column(Text, nullable=False)
    diagnosis = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    treatment = Column(Text, nullable=False)
    follow_up_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], backref="patient_records")
    doctor = relationship("User", foreign_keys=[doctor_id], backref="doctor_records")
    appointment = relationship("Appointment", backref="medical_record")
    prescriptions = relationship("Prescription", back_populates="medical_record", cascade="all, delete-orphan")
    documents = relationship("MedicalDocument", back_populates="medical_record", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MedicalRecord patient_id={self.patient_id} doctor_id={self.doctor_id} date={self.visit_date}>"


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    medical_record_id = Column(UUID(as_uuid=True), ForeignKey("medical_records.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    medicine_name = Column(String(255), nullable=False)
    dosage = Column(String(100), nullable=False)
    frequency = Column(String(100), nullable=False)
    duration = Column(String(100), nullable=False)
    instructions = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    medical_record = relationship("MedicalRecord", back_populates="prescriptions")
    patient = relationship("User", foreign_keys=[patient_id])
    doctor = relationship("User", foreign_keys=[doctor_id])

    def __repr__(self):
        return f"<Prescription medicine={self.medicine_name} patient_id={self.patient_id}>"


class MedicalDocument(Base):
    __tablename__ = "medical_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    medical_record_id = Column(UUID(as_uuid=True), ForeignKey("medical_records.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    document_type = Column(String(50), nullable=False)  # PDF, Image, Lab Report
    file_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    medical_record = relationship("MedicalRecord", back_populates="documents")
    patient = relationship("User", foreign_keys=[patient_id])

    def __repr__(self):
        return f"<MedicalDocument title={self.title} type={self.document_type}>"
