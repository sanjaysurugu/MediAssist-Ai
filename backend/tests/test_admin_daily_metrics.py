from datetime import date, datetime, time, timedelta, timezone

from tests.conftest import TestingSessionLocal
from app.core.security import get_password_hash
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User, UserRole


def test_admin_stats_include_today_patient_registrations_and_appointments(client):
    db = TestingSessionLocal()
    now = datetime.now(timezone.utc)
    admin = User(
        full_name="Dashboard Admin",
        email="daily.admin@example.com",
        password_hash=get_password_hash("AdminSecret123!"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        created_at=now,
    )
    today_patient = User(
        full_name="Today Patient",
        email="today.patient@example.com",
        password_hash=get_password_hash("PatientSecret123!"),
        role=UserRole.PATIENT,
        is_active=True,
        created_at=now,
    )
    old_patient = User(
        full_name="Earlier Patient",
        email="earlier.patient@example.com",
        password_hash=get_password_hash("PatientSecret123!"),
        role=UserRole.PATIENT,
        is_active=True,
        created_at=now - timedelta(days=2),
    )
    doctor = User(
        full_name="Dashboard Doctor",
        email="daily.doctor@example.com",
        password_hash=get_password_hash("DoctorSecret123!"),
        role=UserRole.DOCTOR,
        is_active=True,
        created_at=now,
    )
    db.add_all([admin, today_patient, old_patient, doctor])
    db.flush()
    db.add_all([
        Appointment(
            patient_id=today_patient.id,
            doctor_id=doctor.id,
            appointment_date=date.today(),
            start_time=time(10, 0),
            end_time=time(10, 30),
            reason="Today appointment",
            status=AppointmentStatus.PENDING,
        ),
        Appointment(
            patient_id=old_patient.id,
            doctor_id=doctor.id,
            appointment_date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(10, 30),
            reason="Tomorrow appointment",
            status=AppointmentStatus.PENDING,
        ),
    ])
    db.commit()
    db.close()

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "daily.admin@example.com", "password": "AdminSecret123!"},
    )
    assert login.status_code == 200
    response = client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )

    assert response.status_code == 200
    stats = response.json()
    assert stats["patient_registrations_today"] == 1
    assert stats["appointments_today"] == 1
    assert len(stats["daily_trends"]) == 14
    today_trend = next(
        point for point in stats["daily_trends"]
        if point["date"].startswith(date.today().isoformat())
    )
    assert today_trend["patient_registrations"] == 1
    assert today_trend["appointments"] == 1
