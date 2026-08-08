"""Tests for admin-only scan deletion: findings only ever observed in the deleted scan
are removed with it; findings also observed in another scan are kept and re-anchored."""
from tests.test_scan_series import _import


def test_non_admin_cannot_delete_scan(client, admin_token):
    result = _import(client, admin_token, scan_name="VM-TEST", hostname="host01", plugin_name="Plugin A")

    ro = client.post(
        "/api/users",
        json={"email": "ro2@test.internal", "full_name": "RO", "role": "readonly", "password": "Password123!"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert ro.status_code == 201
    login = client.post("/api/auth/login", json={"email": "ro2@test.internal", "password": "Password123!"})
    ro_token = login.json()["access_token"]

    resp = client.delete(f"/api/scans/{result['scan_id']}", headers={"Authorization": f"Bearer {ro_token}"})
    assert resp.status_code == 403


def test_deleting_unknown_scan_returns_404(client, admin_token):
    resp = client.delete("/api/scans/999999", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 404


def test_deleting_a_scan_removes_findings_only_seen_there(client, admin_token):
    result = _import(client, admin_token, scan_name="VM-TEST", hostname="host01", plugin_name="Plugin A")

    resp = client.delete(f"/api/scans/{result['scan_id']}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 204

    scans = client.get("/api/scans", headers={"Authorization": f"Bearer {admin_token}"}).json()
    assert all(s["id"] != result["scan_id"] for s in scans)

    findings = client.get("/api/findings", params={"page_size": 50}, headers={"Authorization": f"Bearer {admin_token}"}).json()
    assert findings["total"] == 0


def test_deleting_a_baseline_scan_keeps_findings_still_observed_later(client, admin_token):
    baseline = _import(client, admin_token, scan_name="VM-TEST", hostname="host01", plugin_name="Plugin A")
    # Same series, same finding re-observed in a second import.
    current = _import(client, admin_token, scan_name="VM-TEST", hostname="host01", plugin_name="Plugin A")

    resp = client.delete(f"/api/scans/{baseline['scan_id']}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 204

    findings = client.get("/api/findings", params={"page_size": 50}, headers={"Authorization": f"Bearer {admin_token}"}).json()
    assert findings["total"] == 1
    assert findings["items"][0]["scan_id"] == current["scan_id"]

    scans = client.get("/api/scans", headers={"Authorization": f"Bearer {admin_token}"}).json()
    assert any(s["id"] == current["scan_id"] for s in scans)
    assert all(s["id"] != baseline["scan_id"] for s in scans)
