"""Regression tests for the scan-comparison / remediation-detection scoping fix:
importing one scan series must never resolve findings that belong to a different
scan series, even when they share a host, and comparing two scans must reflect
actual per-scan observation membership rather than a finding's last scan_id."""
from tests.test_import import _build_workbook


def _import(client, token, **kwargs):
    files = {
        "file": (
            "scan.xlsx",
            _build_workbook(**kwargs),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    resp = client.post("/api/scans/import", files=files, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _finding_statuses(client, token):
    items = client.get("/api/findings", params={"page_size": 50}, headers={"Authorization": f"Bearer {token}"}).json()[
        "items"
    ]
    return {f["plugin_name"]: f["status"] for f in items}


def test_importing_a_different_scan_series_does_not_resolve_other_series_findings(client, admin_token):
    _import(client, admin_token, scan_name="VM-CAA-INT", hostname="host01", plugin_name="Plugin A")
    _import(client, admin_token, scan_name="VM-CAA-WEB", hostname="host01", plugin_name="Plugin B")

    statuses = _finding_statuses(client, admin_token)
    assert statuses["Plugin A"] == "open"
    assert statuses["Plugin B"] == "open"


def test_reimporting_the_same_scan_series_resolves_missing_findings(client, admin_token):
    _import(client, admin_token, scan_name="VM-CAA-INT", hostname="host01", plugin_name="Plugin A")
    result = _import(client, admin_token, scan_name="VM-CAA-INT", hostname="host01", plugin_name="Plugin C")

    assert result["resolved_findings"] == 1
    statuses = _finding_statuses(client, admin_token)
    assert statuses["Plugin A"] == "remediated"
    assert statuses["Plugin C"] == "open"


def test_scan_compare_endpoint_reflects_observation_membership(client, admin_token):
    baseline = _import(client, admin_token, scan_name="VM-CAA-INT", hostname="host01", plugin_name="Plugin A")
    current = _import(client, admin_token, scan_name="VM-CAA-INT", hostname="host01", plugin_name="Plugin C")

    resp = client.get(
        "/api/scans/compare",
        params={"baseline_scan_id": baseline["scan_id"], "current_scan_id": current["scan_id"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["new_count"] == 1
    assert body["resolved_count"] == 1
    assert body["persisting_count"] == 0
