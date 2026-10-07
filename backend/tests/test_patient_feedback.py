import smtplib

from app.api.v1.endpoints import feedback as feedback_endpoint
from app.core.security import get_password_hash
from app.models.feedback import PatientFeedback
from app.models.user import User, UserRole
from tests.conftest import TestingSessionLocal


def feedback_headers(client, role: UserRole) -> dict[str, str]:
    password = "FeedbackSecret123!"
    db = TestingSessionLocal()
    user = User(
        full_name=f"Feedback {role.value}",
        email=f"feedback.{role.value}@example.com",
        password_hash=get_password_hash(password),
        role=role,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.close()
    login = client.post(
        "/api/v1/auth/login",
        json={"email": f"feedback.{role.value}@example.com", "password": password},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_patient_feedback_is_sent_to_configured_recipient(client, monkeypatch):
    headers = feedback_headers(client, UserRole.PATIENT)
    sent = {}
    monkeypatch.setattr(feedback_endpoint, "feedback_email_configured", lambda: True)
    monkeypatch.setattr(
        feedback_endpoint,
        "send_feedback_email",
        lambda **kwargs: sent.update(kwargs),
    )

    response = client.post(
        "/api/v1/feedback/",
        headers=headers,
        json={
            "category": "Suggestion",
            "rating": 5,
            "message": "The appointment flow is easy to use.",
        },
    )

    assert response.status_code == 202
    assert response.json()["message"].endswith("sanjays60641@gmail.com.")
    assert sent["sender_email"] == "feedback.patient@example.com"
    assert sent["category"] == "Suggestion"
    assert sent["rating"] == 5
    assert sent["feedback"] == "The appointment flow is easy to use."


def test_feedback_is_patient_only(client, monkeypatch):
    headers = feedback_headers(client, UserRole.DOCTOR)
    monkeypatch.setattr(feedback_endpoint, "feedback_email_configured", lambda: True)
    sent = []
    monkeypatch.setattr(feedback_endpoint, "send_feedback_email", lambda **kwargs: sent.append(kwargs))

    response = client.post(
        "/api/v1/feedback/",
        headers=headers,
        json={
            "category": "General feedback",
            "rating": 4,
            "message": "The website is working well.",
        },
    )

    assert response.status_code == 403
    assert sent == []


def test_feedback_is_saved_when_smtp_is_not_configured(client, monkeypatch):
    headers = feedback_headers(client, UserRole.PATIENT)
    monkeypatch.setattr(feedback_endpoint, "feedback_email_configured", lambda: False)

    response = client.post(
        "/api/v1/feedback/",
        headers=headers,
        json={
            "category": "Issue",
            "rating": 2,
            "message": "I had trouble finding the profile settings.",
        },
    )

    assert response.status_code == 202
    assert response.json()["email_status"] == "pending"
    assert "saved" in response.json()["message"].lower()
    db = TestingSessionLocal()
    saved_feedback = db.query(PatientFeedback).one()
    assert saved_feedback.category == "Issue"
    assert saved_feedback.email_status == "pending"
    db.close()


def test_feedback_reports_delivery_failure(client, monkeypatch):
    headers = feedback_headers(client, UserRole.PATIENT)
    monkeypatch.setattr(feedback_endpoint, "feedback_email_configured", lambda: True)

    def fail_to_send(**kwargs):
        raise smtplib.SMTPException("Mail server unavailable")

    monkeypatch.setattr(feedback_endpoint, "send_feedback_email", fail_to_send)
    response = client.post(
        "/api/v1/feedback/",
        headers=headers,
        json={
            "category": "Issue",
            "rating": 1,
            "message": "I cannot complete my appointment booking.",
        },
    )

    assert response.status_code == 202
    assert response.json()["email_status"] == "failed"
    db = TestingSessionLocal()
    saved_feedback = db.query(PatientFeedback).one()
    assert saved_feedback.email_status == "failed"
    db.close()


def test_admin_can_review_and_retry_saved_feedback(client, monkeypatch):
    patient_headers = feedback_headers(client, UserRole.PATIENT)
    monkeypatch.setattr(feedback_endpoint, "feedback_email_configured", lambda: False)
    submitted = client.post(
        "/api/v1/feedback/",
        headers=patient_headers,
        json={
            "category": "Suggestion",
            "rating": 4,
            "message": "Please add more appointment reminders.",
        },
    )
    assert submitted.status_code == 202
    assert client.get("/api/v1/feedback/", headers=patient_headers).status_code == 403

    admin_headers = feedback_headers(client, UserRole.ADMIN)
    listing = client.get("/api/v1/feedback/", headers=admin_headers)
    assert listing.status_code == 200
    entry = listing.json()[0]
    assert entry["category"] == "Suggestion"
    assert entry["patient_email"] == "feedback.patient@example.com"
    assert entry["email_status"] == "pending"

    sent = {}
    monkeypatch.setattr(feedback_endpoint, "feedback_email_configured", lambda: True)
    monkeypatch.setattr(feedback_endpoint, "send_feedback_email", lambda **kwargs: sent.update(kwargs))
    retried = client.post(f"/api/v1/feedback/{entry['id']}/retry-email", headers=admin_headers)
    assert retried.status_code == 200
    assert retried.json()["email_status"] == "sent"
    assert sent["feedback"] == "Please add more appointment reminders."

    updated_listing = client.get("/api/v1/feedback/", headers=admin_headers)
    assert updated_listing.json()[0]["email_status"] == "sent"


def test_retry_without_smtp_does_not_show_configuration_notice(client, monkeypatch):
    patient_headers = feedback_headers(client, UserRole.PATIENT)
    monkeypatch.setattr(feedback_endpoint, "feedback_email_configured", lambda: False)
    submitted = client.post(
        "/api/v1/feedback/",
        headers=patient_headers,
        json={
            "category": "Suggestion",
            "rating": 4,
            "message": "Please add more appointment reminders.",
        },
    )
    assert submitted.status_code == 202

    admin_headers = feedback_headers(client, UserRole.ADMIN)
    listing = client.get("/api/v1/feedback/", headers=admin_headers)
    feedback_id = listing.json()[0]["id"]
    retried = client.post(
        f"/api/v1/feedback/{feedback_id}/retry-email",
        headers=admin_headers,
    )

    assert retried.status_code == 200
    assert retried.json() == {"email_status": "pending"}


def test_feedback_validates_rating_and_message_length(client, monkeypatch):
    headers = feedback_headers(client, UserRole.PATIENT)
    monkeypatch.setattr(feedback_endpoint, "feedback_email_configured", lambda: True)

    response = client.post(
        "/api/v1/feedback/",
        headers=headers,
        json={"category": "Issue", "rating": 6, "message": "Short"},
    )

    assert response.status_code == 422
