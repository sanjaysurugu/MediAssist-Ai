from tests.conftest import TestingSessionLocal
from app.core.security import get_password_hash
from app.models.department import Department
from app.models.user import User, UserRole


def test_phase2_patient_and_doctor_workflow(client):
    # 1. Create Department
    db = TestingSessionLocal()
    dept = Department(name="Neurology", description="Brain & Nerve Care")
    db.add(dept)
    db.commit()
    db.refresh(dept)
    dept_id = str(dept.id)

    # Create Admin User
    admin = User(
        full_name="Admin User",
        email="admin.phase2@hospital.org",
        password_hash=get_password_hash("AdminSecret123!"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    db.add(admin)
    db.commit()
    db.close()

    # 2. Register Patient & Login
    patient_res = client.post("/api/v1/auth/register/patient", json={
        "full_name": "Alice Green",
        "email": "alice.p2@example.com",
        "password": "Password123!",
        "profile": {"blood_group": "A+"}
    })
    assert patient_res.status_code == 201

    pat_login = client.post("/api/v1/auth/login", json={"email": "alice.p2@example.com", "password": "Password123!"})
    patient_token = pat_login.json()["access_token"]

    # 3. Patient Updates Profile via /patients/me
    update_res = client.put("/api/v1/patients/me", 
        json={"emergency_contact": "+19998887777", "address": "742 Evergreen Terrace"},
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["emergency_contact"] == "+19998887777"

    # 4. Register Doctor
    doc_res = client.post("/api/v1/auth/register/doctor", json={
        "full_name": "Dr. Sarah Connor",
        "email": "sarah.connor@hospital.org",
        "password": "Password123!",
        "profile": {
            "specialization": "Neurology",
            "license_number": "DOC-999111",
            "experience_years": 12,
            "qualification": "MD Neurology",
            "consultation_fee": 200.0,
            "department_id": dept_id
        }
    })
    assert doc_res.status_code == 201
    doctor_id = doc_res.json()["doctor_profile"]["id"]

    # 5. Doctor Log In & Toggle Availability
    doc_login = client.post("/api/v1/auth/login", json={"email": "sarah.connor@hospital.org", "password": "Password123!"})
    doc_token = doc_login.json()["access_token"]

    avail_res = client.patch("/api/v1/doctors/me/availability", json={"available": False}, headers={"Authorization": f"Bearer {doc_token}"})
    assert avail_res.status_code == 200
    assert avail_res.json()["available"] is False

    # 6. Patient Searches Doctors
    search_res = client.get(f"/api/v1/doctors?department_id={dept_id}")
    assert search_res.status_code == 200
    docs_list = search_res.json()
    assert len(docs_list) == 1
    assert docs_list[0]["full_name"] == "Dr. Sarah Connor"

    # 7. Admin Login & Stats Dashboard
    admin_login = client.post("/api/v1/auth/login", json={"email": "admin.phase2@hospital.org", "password": "AdminSecret123!"})
    admin_token = admin_login.json()["access_token"]

    stats_res = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_patients"] == 1
    assert stats["total_doctors"] == 1

    # 8. Admin Verifies Doctor
    verify_res = client.patch(f"/api/v1/admin/doctors/{doctor_id}/verify?verify=true", headers={"Authorization": f"Bearer {admin_token}"})
    assert verify_res.status_code == 200
    assert verify_res.json()["is_verified"] is True
