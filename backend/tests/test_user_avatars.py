from uuid import UUID

from app.core.security import get_password_hash
from app.models.user import User, UserAvatar, UserRole
from app.models.profile import DoctorProfile
from app.api.v1.endpoints import users as users_endpoint
from tests.conftest import TestingSessionLocal


def test_each_role_can_upload_and_remove_own_avatar(client, monkeypatch, tmp_path):
    monkeypatch.setattr(users_endpoint, "AVATAR_DIRECTORY", tmp_path)
    password = "AvatarSecret123!"
    roles = [UserRole.PATIENT, UserRole.DOCTOR, UserRole.ADMIN]
    db = TestingSessionLocal()
    db.add_all([
        User(
            full_name=f"Avatar {role.value}",
            email=f"avatar.{role.value}@example.com",
            password_hash=get_password_hash(password),
            role=role,
            is_active=True,
            is_verified=True,
        )
        for role in roles
    ])
    db.commit()
    db.close()

    png_content = b"\x89PNG\r\n\x1a\n" + b"valid test image bytes"
    for role in roles:
        login = client.post(
            "/api/v1/auth/login",
            json={"email": f"avatar.{role.value}@example.com", "password": password},
        )
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        upload = client.post(
            "/api/v1/users/me/avatar",
            headers=headers,
            files={"file": ("profile.png", png_content, "image/png")},
        )
        assert upload.status_code == 200
        avatar_url = upload.json()["avatar_url"]
        assert avatar_url
        current_user = client.get("/api/v1/auth/me", headers=headers)
        user_id = current_user.json()["id"]
        db = TestingSessionLocal()
        stored_avatar = db.query(UserAvatar).filter(
            UserAvatar.user_id == UUID(user_id)
        ).first()
        assert stored_avatar is not None
        assert stored_avatar.image_data == png_content
        db.close()

        assert current_user.json()["avatar_url"] == avatar_url
        photo = client.get(
            f"/api/v1/users/{current_user.json()['id']}/avatar",
            headers=headers,
        )
        assert photo.status_code == 200
        assert photo.content == png_content
        monkeypatch.setattr(users_endpoint, "AVATAR_DIRECTORY", tmp_path / "restarted")
        photo_after_restart = client.get(
            f"/api/v1/users/{current_user.json()['id']}/avatar",
            headers=headers,
        )
        assert photo_after_restart.status_code == 200
        assert photo_after_restart.content == png_content
        monkeypatch.setattr(users_endpoint, "AVATAR_DIRECTORY", tmp_path)
        if role == UserRole.PATIENT:
            doctor_login = client.post(
                "/api/v1/auth/login",
                json={"email": "avatar.doctor@example.com", "password": password},
            )
            doctor_headers = {"Authorization": f"Bearer {doctor_login.json()['access_token']}"}
            denied_photo = client.get(
                f"/api/v1/users/{current_user.json()['id']}/avatar",
                headers=doctor_headers,
            )
            assert denied_photo.status_code == 403

            admin_login = client.post(
                "/api/v1/auth/login",
                json={"email": "avatar.admin@example.com", "password": password},
            )
            admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
            admin_photo = client.get(
                f"/api/v1/users/{current_user.json()['id']}/avatar",
                headers=admin_headers,
            )
            assert admin_photo.status_code == 200

        removal = client.delete("/api/v1/users/me/avatar", headers=headers)
        assert removal.status_code == 200
        assert removal.json()["avatar_url"] is None
        db = TestingSessionLocal()
        assert db.query(UserAvatar).filter(
            UserAvatar.user_id == UUID(current_user.json()["id"])
        ).first() is None
        db.close()


def test_avatar_upload_rejects_non_image_content(client):
    db = TestingSessionLocal()
    user = User(
        full_name="Avatar Patient",
        email="avatar.invalid@example.com",
        password_hash=get_password_hash("AvatarSecret123!"),
        role=UserRole.PATIENT,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.close()
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "avatar.invalid@example.com", "password": "AvatarSecret123!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = client.post(
        "/api/v1/users/me/avatar",
        headers=headers,
        files={"file": ("profile.png", b"not an image", "image/png")},
    )

    assert response.status_code == 400


def test_doctor_directory_serves_database_profile_photo(client):
    image_content = b"\x89PNG\r\n\x1a\nprofile photo"
    avatar_filename = "doctor-profile.png"

    db = TestingSessionLocal()
    doctor = User(
        full_name="Profile Photo Doctor",
        email="profile.photo.doctor@example.com",
        password_hash=get_password_hash("AvatarSecret123!"),
        role=UserRole.DOCTOR,
        is_active=True,
        is_verified=True,
        avatar_url=avatar_filename,
    )
    doctor.avatar = UserAvatar(
        content_type="image/png",
        image_data=image_content,
    )
    doctor_profile = DoctorProfile(
        user=doctor,
        specialization="Cardiology",
        license_number="PHOTO-DOCTOR-001",
        experience_years=5,
        consultation_fee=50,
        available=True,
    )
    db.add(doctor_profile)
    db.commit()
    db.refresh(doctor_profile)
    doctor_profile_id = doctor_profile.id
    db.close()

    listing = client.get("/api/v1/doctors/")
    assert listing.status_code == 200
    doctor_card = next(
        item for item in listing.json() if item["id"] == str(doctor_profile_id)
    )
    assert doctor_card["avatar_url"] == f"/doctors/{doctor_profile_id}/avatar"
    detail = client.get(f"/api/v1/doctors/{doctor_profile_id}")
    assert detail.status_code == 200
    assert detail.json()["avatar_url"] == doctor_card["avatar_url"]

    photo = client.get(f"/api/v1{doctor_card['avatar_url']}")
    assert photo.status_code == 200
    assert photo.headers["content-type"] == "image/png"
    assert photo.content == image_content
