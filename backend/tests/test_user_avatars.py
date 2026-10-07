from app.core.security import get_password_hash
from app.models.user import User, UserRole
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
        avatar_filename = avatar_url
        assert (tmp_path / avatar_filename).read_bytes() == png_content

        current_user = client.get("/api/v1/auth/me", headers=headers)
        assert current_user.json()["avatar_url"] == avatar_url
        photo = client.get(
            f"/api/v1/users/{current_user.json()['id']}/avatar",
            headers=headers,
        )
        assert photo.status_code == 200
        assert photo.content == png_content
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
        assert not (tmp_path / avatar_filename).exists()


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
