from tests.conftest import TestingSessionLocal


def test_phase5_ai_symptom_assistant(client):
    # 1. Register Patient & Login
    p_res = client.post("/api/v1/auth/register/patient", json={
        "full_name": "Charlie Patient",
        "email": "charlie@example.com",
        "password": "Password123!"
    })
    assert p_res.status_code == 201

    p_login = client.post("/api/v1/auth/login", json={"email": "charlie@example.com", "password": "Password123!"})
    patient_token = p_login.json()["access_token"]

    # 2. EMERGENCY TRIGGER TEST (Severe Chest Pain)
    emergency_payload = {
        "symptoms": "I am experiencing severe chest pain and crushing pressure radiating to my left arm.",
        "duration_days": 1,
        "age": 45
    }
    em_res = client.post("/api/v1/ai/symptom-check", json=emergency_payload, headers={"Authorization": f"Bearer {patient_token}"})
    assert em_res.status_code == 200
    em_data = em_res.json()
    assert em_data["is_emergency"] is True
    assert em_data["priority_level"] == "EMERGENCY"
    assert "CALL EMERGENCY SERVICES" in em_data["recommended_next_steps"][0]

    # 3. STANDARD SYMPTOM ANALYSIS TEST (Fever + Cough)
    standard_payload = {
        "symptoms": "I have had a mild fever and cough with a sore throat for 3 days.",
        "duration_days": 3,
        "age": 28
    }
    std_res = client.post("/api/v1/ai/symptom-check", json=standard_payload, headers={"Authorization": f"Bearer {patient_token}"})
    assert std_res.status_code == 200
    std_data = std_res.json()
    assert std_data["is_emergency"] is False
    assert std_data["priority_level"] in ["LOW", "MODERATE", "HIGH"]
    assert len(std_data["detected_symptoms"]) >= 2
    assert "not a diagnostic system" in std_data["disclaimer"].lower()

    # 4. SAFETY GUARD TEST (Ensure no forbidden phrases present)
    forbidden_phrases = ["you definitely have", "you don't need a doctor", "this medicine will cure you"]
    disclaimer_str = std_data["disclaimer"].lower()
    summary_str = std_data["summary"].lower()
    for phrase in forbidden_phrases:
        assert phrase not in summary_str
        assert phrase not in disclaimer_str

    # Symptom analysis is restricted to patient accounts.
    doctor_res = client.post("/api/v1/auth/register/doctor", json={
        "full_name": "Doctor User",
        "email": "doctor.ai@example.com",
        "password": "Password123!",
        "profile": {
            "specialization": "General Medicine",
            "license_number": "AI-DOC-001",
            "experience_years": 1,
            "consultation_fee": 50.0
        }
    })
    assert doctor_res.status_code == 201
    doctor_login = client.post(
        "/api/v1/auth/login",
        json={"email": "doctor.ai@example.com", "password": "Password123!"}
    )
    doctor_token = doctor_login.json()["access_token"]
    doctor_symptom_res = client.post(
        "/api/v1/ai/symptom-check",
        json=standard_payload,
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert doctor_symptom_res.status_code == 403

    # Emergency contacts remain public.
    contacts_res = client.get("/api/v1/ai/emergency-contacts")
    assert contacts_res.status_code == 200
    assert len(contacts_res.json()["contacts"]) > 0
