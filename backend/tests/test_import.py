from io import BytesIO

from openpyxl import Workbook


def _build_workbook() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Vulnérabilités"
    ws.append(["🕒 VULNÉRABILITÉS"])
    ws.append([])
    ws.append(
        [
            "Nom du scan", "Grade", "Score", "Nom du plugin", "CVE", "Grade actif", "Score actif",
            "FQDN", "Nom d'hôte", "IP", "OS", "Protocole", "Port", "Description", "Solution",
            "Version CVSS", "CVSS", "Exploitable",
        ]
    )
    ws.append(
        [
            "VM-TEST", "D", 66, "OpenSSL Vulnerability", "CVE-2024-0001", "C", 61,
            "host01.example.local", "host01", "10.0.0.1", "Linux", "TCP", 443,
            "Test description", "Upgrade OpenSSL", "cvss3", 7.5, "Oui",
        ]
    )

    tags_ws = wb.create_sheet("Analyse des tags des actifs")
    tags_ws.append(["🏷️ ANALYSE"])
    tags_ws.append([])
    tags_ws.append(["Nom de l'actif", "Exposition", "Criticité", "Classification"])
    tags_ws.append(["host01", "Internet", "Critical", "Sensible"])

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def test_parser_extracts_rows_and_asset_context():
    from app.importers.tenable_excel.parser import parse_tenable_workbook

    parsed = parse_tenable_workbook(_build_workbook(), "test.xlsx")
    assert len(parsed.vulnerabilities) == 1
    row = parsed.vulnerabilities[0]
    assert row.hostname == "host01"
    assert row.cve == "CVE-2024-0001"
    assert row.exploitable is True
    assert "host01" in parsed.asset_context
    assert parsed.asset_context["host01"].exposition == "Internet"


def test_import_endpoint_creates_scan_and_scored_finding(client, admin_token):
    files = {
        "file": (
            "scan.xlsx",
            _build_workbook(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    resp = client.post(
        "/api/scans/import", files=files, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["new_findings"] == 1
    assert body["row_count"] == 1

    findings_resp = client.get("/api/findings", headers={"Authorization": f"Bearer {admin_token}"})
    assert findings_resp.status_code == 200
    items = findings_resp.json()["items"]
    assert len(items) == 1
    finding = items[0]
    # CVSS 7.5 + internet (1.5) + critical (2.5) + exploitable (2.0) = 13.5 -> clamped to 10
    assert finding["caa_score"] == 10.0
    assert finding["caa_severity"] == "Critique"
    assert finding["hostname"] == "host01"
