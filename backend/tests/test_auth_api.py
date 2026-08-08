def test_login_success(client):
    resp = client.post("/api/auth/login", json={"email": "admin@test.internal", "password": "Password123!"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["role"] == "admin"


def test_login_wrong_password_rejected(client):
    resp = client.post("/api/auth/login", json={"email": "admin@test.internal", "password": "wrong"})
    assert resp.status_code == 401


def test_protected_endpoint_requires_token(client):
    resp = client.get("/api/findings")
    assert resp.status_code == 401


def test_me_endpoint_returns_current_user(client, admin_token):
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "admin@test.internal"


def test_non_admin_cannot_create_user(client, admin_token):
    # create a readonly user then try to use it to create another user
    create_resp = client.post(
        "/api/users",
        json={"email": "ro@test.internal", "full_name": "RO", "role": "readonly", "password": "Password123!"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_resp.status_code == 201

    login_resp = client.post("/api/auth/login", json={"email": "ro@test.internal", "password": "Password123!"})
    ro_token = login_resp.json()["access_token"]

    forbidden = client.post(
        "/api/users",
        json={"email": "x@test.internal", "full_name": "X", "role": "readonly", "password": "Password123!"},
        headers={"Authorization": f"Bearer {ro_token}"},
    )
    assert forbidden.status_code == 403
