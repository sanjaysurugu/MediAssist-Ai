from app.schemas.auth import LoginRequest, RefreshTokenRequest, Token, TokenPayload
from app.schemas.user import (
    UserBase, PatientRegisterRequest, DoctorRegisterRequest, UserOut, UserUpdate,
    DoctorPublicOut, UserStatusUpdate, AdminDashboardStats
)
from app.schemas.profile import (
    PatientProfileOut, PatientProfileUpdate, DoctorProfileOut, DoctorProfileUpdate, DoctorAvailabilityUpdate
)
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentOut
from app.schemas.audit import AuditLogOut
from app.schemas.appointment import (
    AppointmentCreate, AppointmentUpdateStatus, AppointmentOut, AppointmentUserSummary, TimeSlot
)
from app.schemas.medical_record import (
    PrescriptionCreate, PrescriptionOut,
    MedicalDocumentCreate, MedicalDocumentOut,
    MedicalRecordCreate, MedicalRecordUpdate, MedicalRecordOut
)

__all__ = [
    "LoginRequest", "RefreshTokenRequest", "Token", "TokenPayload",
    "UserBase", "PatientRegisterRequest", "DoctorRegisterRequest", "UserOut", "UserUpdate",
    "DoctorPublicOut", "UserStatusUpdate", "AdminDashboardStats",
    "PatientProfileOut", "PatientProfileUpdate", "DoctorProfileOut", "DoctorProfileUpdate", "DoctorAvailabilityUpdate",
    "DepartmentCreate", "DepartmentUpdate", "DepartmentOut",
    "AuditLogOut",
    "AppointmentCreate", "AppointmentUpdateStatus", "AppointmentOut", "AppointmentUserSummary", "TimeSlot",
    "PrescriptionCreate", "PrescriptionOut", "MedicalDocumentCreate", "MedicalDocumentOut",
    "MedicalRecordCreate", "MedicalRecordUpdate", "MedicalRecordOut"
]
