from tests.conftest import TestingSessionLocal
from app.models.department import Department


def test_health_check_and_disclaimer(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "medical_disclaimer" in data
    assert "not a diagnostic system" in data["medical_disclaimer"]


def test_patient_registration_and_login(client):
    # 1. Register Patient
    patient_payload = {
        "full_name": "Jane Doe",
        "email": "jane.doe@example.com",
        "phone": "+19876543210",
        "password": "SecurePassword123!",
        "profile": {
            "date_of_birth": "1995-05-15",
            "gender": "Female",
            "blood_group": "O+",
            "emergency_contact": "+19876543211",
            "address": "123 Health Ave, Medical City"
        }
    }
    reg_response = client.post("/api/v1/auth/register/patient", json=patient_payload)
    assert reg_response.status_code == 201
    reg_data = reg_response.json()
    assert reg_data["email"] == "jane.doe@example.com"
    assert reg_data["role"] == "patient"
    assert reg_data["patient_profile"]["blood_group"] == "O+"

    # 2. Login as Patient
    login_response = client.post("/api/v1/auth/login", json={
        "email": "jane.doe@example.com",
        "password": "SecurePassword123!"
    })
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data
    assert login_data["role"] == "patient"

    # 3. Access Protected Route /me
    token = login_data["access_token"]
    me_response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["full_name"] == "Jane Doe"


def test_doctor_registration_and_department(client):
    # 1. Create Department as Admin (or direct DB seed)
    db = TestingSessionLocal()
    dept = Department(name="Cardiology", description="Heart Care")
    db.add(dept)
    db.commit()
    db.refresh(dept)
    dept_id = str(dept.id)
    db.close()

    # 2. Register Doctor
    doctor_payload = {
        "full_name": "Dr. John Smith",
        "email": "john.smith@hospital.org",
        "phone": "+15550001111",
        "password": "DoctorPassword123!",
        "profile": {
            "specialization": "Cardiology",
            "license_number": "MED-123456",
            "experience_years": 10,
            "qualification": "MD Cardiology",
            "consultation_fee": 150.0,
            "bio": "Experienced cardiologist specializing in preventive heart health.",
            "available": True,
            "department_id": dept_id
        }
    }
    doc_response = client.post("/api/v1/auth/register/doctor", json=doctor_payload)
    assert doc_response.status_code == 201
    doc_data = doc_response.json()
    assert doc_data["role"] == "doctor"
    assert doc_data["doctor_profile"]["license_number"] == "MED-123456"
