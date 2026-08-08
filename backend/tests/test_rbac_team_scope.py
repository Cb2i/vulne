"""Regression tests for the team_manager RBAC gap: a team manager account with no
team assigned must see nothing, not fall through to global access."""
from tests.test_import import _build_workbook


def _import_one_finding(client, admin_token):
    files = {
        "file": (
            "scan.xlsx",
            _build_workbook(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    resp = client.post("/api/scans/import", files=files, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200, resp.text


def _create_team_manager(client, admin_token, email="tm@test.internal", team_id=None):
    resp = client.post(
        "/api/users",
        json={
            "email": email,
            "full_name": "Team Manager",
            "role": "team_manager",
            "team_id": team_id,
            "password": "Password123!",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201, resp.text
    login = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    assert login.status_code == 200
    return login.json()["access_token"]


def test_team_manager_without_team_sees_no_findings(client, admin_token):
    _import_one_finding(client, admin_token)
    tm_token = _create_team_manager(client, admin_token, team_id=None)

    resp = client.get("/api/findings", headers={"Authorization": f"Bearer {tm_token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["items"] == []


def test_team_manager_without_team_gets_empty_kpi(client, admin_token):
    _import_one_finding(client, admin_token)
    tm_token = _create_team_manager(client, admin_token, team_id=None)

    resp = client.get("/api/kpi/summary", headers={"Authorization": f"Bearer {tm_token}"})
    assert resp.status_code == 200
    assert resp.json()["total_open_findings"] == 0


def test_team_manager_without_team_is_denied_finding_detail(client, admin_token):
    _import_one_finding(client, admin_token)
    admin_findings = client.get("/api/findings", headers={"Authorization": f"Bearer {admin_token}"}).json()["items"]
    finding_id = admin_findings[0]["id"]

    tm_token = _create_team_manager(client, admin_token, team_id=None)
    resp = client.get(f"/api/findings/{finding_id}", headers={"Authorization": f"Bearer {tm_token}"})
    assert resp.status_code == 403


def test_team_manager_with_team_only_sees_own_team(client, admin_token):
    _import_one_finding(client, admin_token)
    admin_findings = client.get("/api/findings", headers={"Authorization": f"Bearer {admin_token}"}).json()["items"]
    finding_id = admin_findings[0]["id"]
    asset_id = admin_findings[0]["asset_id"]

    team = client.post(
        "/api/teams", json={"name": "Réseau"}, headers={"Authorization": f"Bearer {admin_token}"}
    ).json()
    client.patch(
        f"/api/assets/{asset_id}", json={"team_id": team["id"]}, headers={"Authorization": f"Bearer {admin_token}"}
    )

    other_team = client.post(
        "/api/teams", json={"name": "Applications"}, headers={"Authorization": f"Bearer {admin_token}"}
    ).json()
    tm_token = _create_team_manager(client, admin_token, email="tm2@test.internal", team_id=other_team["id"])

    resp = client.get("/api/findings", headers={"Authorization": f"Bearer {tm_token}"})
    assert resp.json()["total"] == 0

    detail = client.get(f"/api/findings/{finding_id}", headers={"Authorization": f"Bearer {tm_token}"})
    assert detail.status_code == 403
