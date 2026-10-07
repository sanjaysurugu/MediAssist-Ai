from fastapi import APIRouter
from app.api.v1.endpoints import admin, ai, appointments, audit, auth, departments, doctors, feedback, patients, records, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Symptom Assistant"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patient Management"])
api_router.include_router(doctors.router, prefix="/doctors", tags=["Doctor Directory & Dashboard"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["Appointment Booking"])
api_router.include_router(records.router, prefix="/records", tags=["Medical Records & Prescriptions"])
api_router.include_router(departments.router, prefix="/departments", tags=["Departments"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin Portal"])
api_router.include_router(users.router, prefix="/users", tags=["Users & Profiles"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["Patient Feedback"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit Logs"])
