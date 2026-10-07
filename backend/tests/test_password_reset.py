import hashlib
from datetime import datetime, timedelta, timezone

import pytest

from app.api.v1.endpoints import auth as auth_endpoint
from app.core.security import get_password_hash, verify_password
from app.models.password_reset import PasswordResetToken
from app.models.user import User, UserRole
from tests.conftest import TestingSessionLocal


def create_user(role: UserRole, email: str) -> None:
    db = TestingSessionLocal()
    db.add(User(
        full_name=f"Reset {role.value}",
        email=email,
        password_hash=get_password_hash("OriginalPassword123!"),
        role=role,
        is_active=True,
        is_verified=True,
    ))
    db.commit()
    db.close()


@pytest.mark.parametrize("role", [UserRole.PATIENT, UserRole.DOCTOR])
def test_patient_and_doctor_can_reset_password_once(client, monkeypatch, role):
    email = f"reset.{role.value}@example.com"
    create_user(role, email)
    sent_messages = []
    monkeypatch.setattr(auth_endpoint, "password_reset_email_configured", lambda: True)
    monkeypatch.setattr(
        auth_endpoint,
        "send_password_reset_email",
        lambda recipient, reset_url: sent_messages.append((recipient, reset_url)),
    )

    request = client.post("/api/v1/auth/password/forgot", json={"email": email})
    assert request.status_code == 202
    assert request.json()["message"].startswith("If an active")
    assert len(sent_messages) == 1
    recipient, reset_url = sent_messages[0]
    assert recipient == email
    token = reset_url.rsplit("/", 1)[-1]
    assert len(token) >= 32

    db = TestingSessionLocal()
    stored_token = db.query(PasswordResetToken).one()
    assert stored_token.token_hash == hashlib.sha256(token.encode()).hexdigest()
    assert stored_token.token_hash != token
    db.close()

    reset = client.post(
        "/api/v1/auth/password/reset",
        json={"token": token, "new_password": "NewSecurePassword123!"},
    )
    assert reset.status_code == 200
    assert client.post(
        "/api/v1/auth/password/reset",
        json={"token": token, "new_password": "AnotherPassword123!"},
    ).status_code == 400

    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == email).one()
    assert verify_password("NewSecurePassword123!", user.password_hash)
    db.close()
    assert client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "NewSecurePassword123!"},
    ).status_code == 200


def test_unknown_account_gets_same_response_without_email(client, monkeypatch):
    sent_messages = []
    monkeypatch.setattr(auth_endpoint, "password_reset_email_configured", lambda: True)
    monkeypatch.setattr(
        auth_endpoint,
        "send_password_reset_email",
        lambda recipient, reset_url: sent_messages.append(recipient),
    )

    response = client.post(
        "/api/v1/auth/password/forgot",
        json={"email": "not.registered@example.com"},
    )

    assert response.status_code == 202
    assert response.json()["message"] == (
        "If an active patient or doctor account exists for that email, "
        "a password reset link will be sent."
    )
    assert sent_messages == []


def test_reset_rejects_expired_token(client, monkeypatch):
    create_user(UserRole.PATIENT, "expired.reset@example.com")
    raw_token = "expired-link-token-that-is-long-enough"
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "expired.reset@example.com").one()
    db.add(PasswordResetToken(
        user_id=user.id,
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    ))
    db.commit()
    db.close()
    monkeypatch.setattr(auth_endpoint, "password_reset_email_configured", lambda: True)

    response = client.post(
        "/api/v1/auth/password/reset",
        json={"token": raw_token, "new_password": "NewSecurePassword123!"},
    )

    assert response.status_code == 400


def test_forgot_password_reports_missing_smtp_configuration(client, monkeypatch):
    monkeypatch.setattr(auth_endpoint, "password_reset_email_configured", lambda: False)

    response = client.post(
        "/api/v1/auth/password/forgot",
        json={"email": "anyone@example.com"},
    )

    assert response.status_code == 503
