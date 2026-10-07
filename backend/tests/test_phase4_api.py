from datetime import date
from tests.conftest import TestingSessionLocal
from app.models.department import Department


def test_phase4_medical_records_prescriptions_and_security(client):
    # 1. Setup Department & Users
    db = TestingSessionLocal()
    dept = Department(name="Dermatology", description="Skin Health")
    db.add(dept)
    db.commit()
    db.refresh(dept)
    dept_id = str(dept.id)
    db.close()

    # Register Patient A
    p_a_res = client.post("/api/v1/auth/register/patient", json={
        "full_name": "Patient Alpha",
        "email": "alpha@example.com",
        "password": "Password123!"
    })
    assert p_a_res.status_code == 201
    patient_a_id = p_a_res.json()["id"]

    p_a_login = client.post("/api/v1/auth/login", json={"email": "alpha@example.com", "password": "Password123!"})
    token_patient_a = p_a_login.json()["access_token"]

    # Register Patient B
    p_b_res = client.post("/api/v1/auth/register/patient", json={
        "full_name": "Patient Beta",
        "email": "beta@example.com",
        "password": "Password123!"
    })
    assert p_b_res.status_code == 201

    p_b_login = client.post("/api/v1/auth/login", json={"email": "beta@example.com", "password": "Password123!"})
    token_patient_b = p_b_login.json()["access_token"]

    # Register Doctor
    doc_res = client.post("/api/v1/auth/register/doctor", json={
        "full_name": "Dr. Derm Specialist",
        "email": "derm@hospital.org",
        "password": "Password123!",
        "profile": {
            "specialization": "Dermatology",
            "license_number": "DERM-888",
            "experience_years": 6,
            "consultation_fee": 100.0,
            "department_id": dept_id
        }
    })
    assert doc_res.status_code == 201
    d_login = client.post("/api/v1/auth/login", json={"email": "derm@hospital.org", "password": "Password123!"})
    token_doctor = d_login.json()["access_token"]

    # 2. Doctor Creates Medical Record with Embedded Prescription for Patient A
    record_payload = {
        "patient_id": patient_a_id,
        "visit_date": str(date.today()),
        "symptoms": "Skin rash and localized itching on arms.",
        "diagnosis": "Mild Contact Dermatitis",
        "notes": "Patient reported starting a new body lotion 3 days ago.",
        "treatment": "Topical hydrocortisone cream application.",
        "follow_up_date": str(date.today()),
        "prescriptions": [
            {
                "medicine_name": "Hydrocortisone 1% Cream",
                "dosage": "Apply thin layer",
                "frequency": "Twice daily",
                "duration": "7 days",
                "instructions": "Apply after washing affected area."
            }
        ]
    }
    rec_res = client.post("/api/v1/records/", json=record_payload, headers={"Authorization": f"Bearer {token_doctor}"})
    assert rec_res.status_code == 201
    rec_data = rec_res.json()
    assert rec_data["diagnosis"] == "Mild Contact Dermatitis"
    assert len(rec_data["prescriptions"]) == 1
    record_id = rec_data["id"]

    # 3. Patient A Views Own Medical Records
    my_records_res = client.get("/api/v1/records/my", headers={"Authorization": f"Bearer {token_patient_a}"})
    assert my_records_res.status_code == 200
    assert len(my_records_res.json()) == 1
    assert my_records_res.json()[0]["id"] == record_id

    # 4. SECURE AUTHORIZATION TEST: Patient B attempts to view Patient A's record -> Expect 403 Forbidden
    unauthorized_res = client.get(f"/api/v1/records/{record_id}", headers={"Authorization": f"Bearer {token_patient_b}"})
    assert unauthorized_res.status_code == 403
    assert "access denied" in unauthorized_res.json()["detail"].lower()

    # 5. Doctor Adds Additional Prescription to Record
    add_p_res = client.post(f"/api/v1/records/{record_id}/prescriptions", json={
        "medicine_name": "Cetirizine 10mg",
        "dosage": "1 Tablet",
        "frequency": "Once daily at bedtime",
        "duration": "5 days",
        "instructions": "For itching relief."
    }, headers={"Authorization": f"Bearer {token_doctor}"})
    assert add_p_res.status_code == 201
    assert add_p_res.json()["medicine_name"] == "Cetirizine 10mg"

    # 6. Patient Uploads Medical Document Metadata
    doc_upload_res = client.post("/api/v1/records/documents/upload", json={
        "medical_record_id": record_id,
        "title": "Allergy Test Report PDF",
        "document_type": "PDF",
        "file_path": "/uploads/documents/allergy_report.pdf",
        "file_size_bytes": 102400
    }, headers={"Authorization": f"Bearer {token_patient_a}"})
    assert doc_upload_res.status_code == 201
    assert doc_upload_res.json()["title"] == "Allergy Test Report PDF"
