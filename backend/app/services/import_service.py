"""Orchestrates a full Tenable Excel import: parse -> upsert assets -> upsert findings
-> apply CAA/SLE/ownership/exceptions -> record scan + import history."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.importers.tenable_excel.parser import ParsedImport, parse_tenable_workbook
from app.models.asset import Asset
from app.models.enums import FindingStatus, ImportStatus
from app.models.finding import Finding
from app.models.import_history import ImportHistory
from app.models.scan import Scan
from app.repositories.asset_repo import get_or_create_asset
from app.services.decommission_service import decommission_asset
from app.services.scoring_service import score_finding


def _identity_key(hostname_to_asset_id: dict[str, int], hostname: str, plugin_name: str, port: int | None):
    return (hostname_to_asset_id[hostname], plugin_name, port)


def import_tenable_workbook(
    db: Session, *, file_bytes: bytes, filename: str, imported_by_id: int | None
) -> tuple[Scan, ImportHistory]:
    parsed: ParsedImport = parse_tenable_workbook(file_bytes, filename)
    now = datetime.now(timezone.utc)

    scan_name = parsed.vulnerabilities[0].scan_name if parsed.vulnerabilities else filename
    scan = Scan(
        name=scan_name,
        source_filename=filename,
        imported_by_id=imported_by_id,
        imported_at=now,
        finding_count=len(parsed.vulnerabilities),
        status=ImportStatus.SUCCESS if parsed.vulnerabilities else ImportStatus.FAILED,
    )
    db.add(scan)
    db.flush()

    hostname_to_asset_id: dict[str, int] = {}
    new_count = 0
    updated_count = 0

    for row in parsed.vulnerabilities:
        context = parsed.asset_context.get(row.hostname)
        asset_defaults = {
            "fqdn": row.fqdn,
            "ip_address": row.ip_address,
            "os": row.os,
            "grade_actif": row.grade_actif,
            "score_actif": row.score_actif,
            "last_seen_at": now,
        }
        if context:
            asset_defaults["exposition"] = context.exposition or "Internal"
            asset_defaults["criticite"] = context.criticite or "Medium"
            asset_defaults["classification"] = context.classification

        asset = get_or_create_asset(db, hostname=row.hostname, defaults=asset_defaults)
        hostname_to_asset_id[row.hostname] = asset.id

        existing = db.scalar(
            select(Finding).where(
                Finding.asset_id == asset.id,
                Finding.plugin_name == row.plugin_name,
                Finding.port == row.port,
                Finding.status.in_([FindingStatus.OPEN, FindingStatus.EXCEPTION]),
            )
        )

        if existing:
            existing.scan_id = scan.id
            existing.cve = row.cve
            existing.grade = row.grade
            existing.score = row.score
            existing.description = row.description
            existing.solution = row.solution
            existing.cvss_version = row.cvss_version
            existing.cvss = row.cvss
            existing.exploitable = row.exploitable
            existing.last_seen_at = now
            finding = existing
            updated_count += 1
        else:
            finding = Finding(
                scan_id=scan.id,
                asset_id=asset.id,
                plugin_name=row.plugin_name,
                cve=row.cve,
                grade=row.grade,
                score=row.score,
                protocol=row.protocol,
                port=row.port,
                description=row.description,
                solution=row.solution,
                cvss_version=row.cvss_version,
                cvss=row.cvss,
                exploitable=row.exploitable,
                status=FindingStatus.OPEN,
                first_seen_at=now,
                last_seen_at=now,
            )
            db.add(finding)
            db.flush()
            new_count += 1

        score_finding(db, finding, asset)

    # Findings from prior scans that no longer appear in this import are resolved.
    resolved_count = 0
    seen_identities = {
        (hostname_to_asset_id[row.hostname], row.plugin_name, row.port) for row in parsed.vulnerabilities
    }
    still_open = db.scalars(
        select(Finding).where(Finding.status.in_([FindingStatus.OPEN, FindingStatus.EXCEPTION]))
    )
    for f in still_open:
        if f.scan_id == scan.id:
            continue
        if (f.asset_id, f.plugin_name, f.port) not in seen_identities and f.asset_id in hostname_to_asset_id.values():
            f.status = FindingStatus.REMEDIATED
            f.resolved_at = now
            resolved_count += 1

    for hostname in parsed.decommissioned_hostnames:
        decommission_asset(
            db, hostname=hostname, reason="Import Tenable — feuille Décommissionés",
            decommissioned_at=None, decommissioned_by_id=imported_by_id,
        )

    history = ImportHistory(
        scan_id=scan.id,
        filename=filename,
        imported_by_id=imported_by_id,
        imported_at=now,
        row_count=len(parsed.vulnerabilities),
        new_findings=new_count,
        updated_findings=updated_count,
        resolved_findings=resolved_count,
        status=scan.status,
        error_details="; ".join(parsed.warnings) if parsed.warnings else None,
    )
    db.add(history)
    db.commit()
    db.refresh(scan)
    db.refresh(history)
    return scan, history
