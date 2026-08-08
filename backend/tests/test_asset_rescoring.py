"""Regression tests for asset edits (exposition/criticité/team) triggering a rescore of
that asset's open findings, and for a manual team assignment surviving rescoring."""
from tests.test_import import _build_workbook


def _import_and_get_finding(client, admin_token):
    files = {
        "file": (
            "scan.xlsx",
            _build_workbook(exposition="Internet", criticite="Critical"),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    resp = client.post("/api/scans/import", files=files, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200, resp.text
    items = client.get("/api/findings", headers={"Authorization": f"Bearer {admin_token}"}).json()["items"]
    return items[0]


def test_editing_asset_exposition_rescopes_open_finding_score(client, admin_token):
    finding = _import_and_get_finding(client, admin_token)
    original_score = finding["caa_score"]
    assert original_score == 10.0  # CVSS 7.5 + Internet(1.5) + Critical(2.5) + exploitable(2.0), clamped

    resp = client.patch(
        f"/api/assets/{finding['asset_id']}",
        json={"exposition": "Airgapped", "criticite": "Low"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200

    updated = client.get(f"/api/findings/{finding['id']}", headers={"Authorization": f"Bearer {admin_token}"}).json()
    assert updated["caa_score"] < original_score


def test_manual_team_assignment_persists_through_later_rescoring(client, admin_token):
    finding = _import_and_get_finding(client, admin_token)
    team = client.post(
        "/api/teams", json={"name": "Postes"}, headers={"Authorization": f"Bearer {admin_token}"}
    ).json()

    client.patch(
        f"/api/assets/{finding['asset_id']}",
        json={"team_id": team["id"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    after_assignment = client.get(
        f"/api/findings/{finding['id']}", headers={"Authorization": f"Bearer {admin_token}"}
    ).json()
    assert after_assignment["team_id"] == team["id"]

    # Editing an unrelated field (exposition) triggers a rescore; the manual team
    # assignment must not be silently overwritten by ownership-rule resolution.
    client.patch(
        f"/api/assets/{finding['asset_id']}",
        json={"exposition": "DMZ"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    after_rescore = client.get(
        f"/api/findings/{finding['id']}", headers={"Authorization": f"Bearer {admin_token}"}
    ).json()
    assert after_rescore["team_id"] == team["id"]
