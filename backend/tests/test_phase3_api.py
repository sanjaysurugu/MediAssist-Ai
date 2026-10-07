from datetime import date, timedelta
from tests.conftest import TestingSessionLocal
from app.core.security import get_password_hash
from app.models.department import Department
from app.models.user import User, UserRole


def test_phase3_appointment_workflow_and_double_booking(client):
    # 1. Setup Department, Doctor, and Patient
    db = TestingSessionLocal()
    dept = Department(name="Pediatrics", description="Children Care")
    db.add(dept)
    db.commit()
    db.refresh(dept)
    dept_id = str(dept.id)
    db.close()

    # Register Patient
    p_res = client.post("/api/v1/auth/register/patient", json={
        "full_name": "Bob Patient",
        "email": "bob.patient@example.com",
        "password": "Password123!"
    })
    assert p_res.status_code == 201
    patient_id = p_res.json()["id"]

    p_login = client.post("/api/v1/auth/login", json={"email": "bob.patient@example.com", "password": "Password123!"})
    patient_token = p_login.json()["access_token"]

    # Register Doctor
    d_res = client.post("/api/v1/auth/register/doctor", json={
        "full_name": "Dr. Emily Stone",
        "email": "emily.stone@hospital.org",
        "password": "Password123!",
        "profile": {
            "specialization": "Pediatrics",
            "license_number": "PED-777",
            "experience_years": 8,
            "consultation_fee": 120.0,
            "department_id": dept_id
        }
    })
    assert d_res.status_code == 201
    doctor_user_id = d_res.json()["id"]

    d_login = client.post("/api/v1/auth/login", json={"email": "emily.stone@hospital.org", "password": "Password123!"})
    doctor_token = d_login.json()["access_token"]

    target_date = str(date.today() + timedelta(days=2))

    # 2. Check Available Time Slots
    slots_res = client.get(f"/api/v1/appointments/available-slots?doctor_id={doctor_user_id}&date={target_date}")
    assert slots_res.status_code == 200
    slots = slots_res.json()
    assert len(slots) > 0
    assert slots[0]["is_available"] is True

    # 3. Patient Books Appointment
    apt_payload = {
        "doctor_id": doctor_user_id,
        "appointment_date": target_date,
        "start_time": "10:00:00",
        "end_time": "10:30:00",
        "reason": "Routine child checkup and fever check."
    }
    book_res = client.post("/api/v1/appointments/", json=apt_payload, headers={"Authorization": f"Bearer {patient_token}"})
    assert book_res.status_code == 201
    apt_data = book_res.json()
    assert apt_data["status"] == "pending"
    apt_id = apt_data["id"]

    doctor_patients = client.get(
        "/api/v1/records/patients",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert doctor_patients.status_code == 200
    assert [patient["id"] for patient in doctor_patients.json()] == [patient_id]

    patient_cannot_list_doctor_patients = client.get(
        "/api/v1/records/patients",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert patient_cannot_list_doctor_patients.status_code == 403

    # 4. Attempt DOUBLE BOOKING (Same doctor, date, and start_time) -> Expect 409 Conflict
    double_res = client.post("/api/v1/appointments/", json=apt_payload, headers={"Authorization": f"Bearer {patient_token}"})
    assert double_res.status_code == 409
    assert "already booked" in double_res.json()["detail"].lower()

    # 5. Doctor Confirms Appointment
    confirm_res = client.patch(f"/api/v1/appointments/{apt_id}/status", json={"status": "confirmed", "notes": "Approved for 10:00 AM slot."}, headers={"Authorization": f"Bearer {doctor_token}"})
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "confirmed"

    # 6. Patient Views Appointments History
    my_apts = client.get("/api/v1/appointments/my", headers={"Authorization": f"Bearer {patient_token}"})
    assert my_apts.status_code == 200
    assert len(my_apts.json()) == 1

    # 7. Doctor Marks Appointment Completed
    complete_res = client.patch(f"/api/v1/appointments/{apt_id}/status", json={"status": "completed", "notes": "Patient attended and prescribed general vitamins."}, headers={"Authorization": f"Bearer {doctor_token}"})
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "completed"
