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
from app.models.scan_observation import ScanObservation
from app.services.decommission_service import decommission_asset
from app.services.rule_import_service import upsert_exceptions, upsert_ownership_rules
from app.services.scoring_service import load_scoring_context, score_finding


def import_tenable_workbook(
    db: Session, *, file_bytes: bytes, filename: str, imported_by_id: int | None
) -> tuple[Scan, ImportHistory, int, int]:
    """Returns (scan, history, imported_ownership_rules, imported_exceptions)."""
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

    # Ownership rules and exceptions are persisted *before* scoring findings below, so a
    # workbook's own "KPI" and "Exceptions" sheets apply immediately to the findings it
    # is about to create -- and to every future scan, since they're now stored in the
    # database rather than re-derived from this one file each time.
    imported_ownership_rules = upsert_ownership_rules(db, parsed.ownership_rules)
    imported_exceptions = upsert_exceptions(db, parsed.exceptions, imported_by_id=imported_by_id)

    # Loaded once and reused for every row below -- with tens of thousands of rows,
    # reloading the CAA config / SLE rules / ownership rules / exceptions per row turned
    # imports that should take a few seconds into ones taking well over a minute.
    scoring_context = load_scoring_context(db)

    # Bulk-load every asset and open/exception finding this import could possibly touch,
    # up front, instead of running a SELECT per row (27k rows -> 27k+ round trips
    # otherwise). Everything below this point works purely against these in-memory
    # dicts; nothing is flushed until the single db.flush() after the main loop.
    hostnames = {row.hostname for row in parsed.vulnerabilities}
    assets_by_hostname: dict[str, Asset] = {
        a.hostname: a for a in db.scalars(select(Asset).where(Asset.hostname.in_(hostnames)))
    }
    preexisting_asset_ids = [a.id for a in assets_by_hostname.values()]
    id_to_hostname = {a.id: h for h, a in assets_by_hostname.items()}

    finding_index: dict[tuple[str, str, int | None], Finding] = {}
    if preexisting_asset_ids:
        preexisting_findings = db.scalars(
            select(Finding).where(
                Finding.asset_id.in_(preexisting_asset_ids),
                Finding.status.in_([FindingStatus.OPEN, FindingStatus.EXCEPTION]),
            )
        )
        for f in preexisting_findings:
            finding_index[(id_to_hostname[f.asset_id], f.plugin_name, f.port)] = f

    observed_finding_objects: set[int] = set()  # keyed by Python id() -- see note below
    scan_observations: list[ScanObservation] = []
    new_count = 0
    updated_count = 0

    for row in parsed.vulnerabilities:
        asset_ctx = parsed.asset_context.get(row.hostname)
        asset_defaults = {
            "fqdn": row.fqdn,
            "ip_address": row.ip_address,
            "os": row.os,
            "grade_actif": row.grade_actif,
            "score_actif": row.score_actif,
            "last_seen_at": now,
        }
        if asset_ctx:
            asset_defaults["exposition"] = asset_ctx.exposition or "Internal"
            asset_defaults["criticite"] = asset_ctx.criticite or "Medium"
            asset_defaults["classification"] = asset_ctx.classification

        asset = assets_by_hostname.get(row.hostname)
        if asset is None:
            asset = Asset(hostname=row.hostname, **asset_defaults)
            db.add(asset)
            assets_by_hostname[row.hostname] = asset
        else:
            for key, value in asset_defaults.items():
                if value not in (None, ""):
                    setattr(asset, key, value)

        finding_key = (row.hostname, row.plugin_name, row.port)
        existing = finding_index.get(finding_key)

        if existing:
            # Note: scan_id is intentionally left untouched — it records the scan this
            # finding was first observed in. Per-scan membership (needed for comparison
            # and for scoping remediation detection below) is tracked via ScanObservation.
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
                asset=asset,  # relationship, not asset_id: asset.id may not exist yet
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
            finding_index[finding_key] = finding
            new_count += 1

        score_finding(finding, asset, scoring_context)

        # Dedup by Python object identity rather than finding.id: finding.id doesn't
        # exist yet for a brand-new finding until the flush below.
        if id(finding) not in observed_finding_objects:
            scan_observations.append(ScanObservation(scan=scan, finding=finding, observed_at=now))
            observed_finding_objects.add(id(finding))

    db.add_all(scan_observations)
    db.flush()
    observed_finding_ids = {so.finding_id for so in scan_observations}

    # A finding is only auto-resolved if it belongs to the same recurring scan series
    # (same "Nom du scan") and is absent from this import. Scoping by scan name — rather
    # than by "this import happened to touch that asset" — prevents importing one scan
    # (e.g. a web-scope scan) from closing findings that belong to a different scan
    # (e.g. an internal-scope scan) just because they share a host.
    resolved_count = 0
    prior_series_finding_ids = set(
        db.scalars(
            select(ScanObservation.finding_id)
            .join(Scan, Scan.id == ScanObservation.scan_id)
            .where(Scan.name == scan.name, ScanObservation.scan_id != scan.id)
        )
    )
    if prior_series_finding_ids:
        still_open = db.scalars(
            select(Finding).where(
                Finding.id.in_(prior_series_finding_ids),
                Finding.status.in_([FindingStatus.OPEN, FindingStatus.EXCEPTION]),
            )
        )
        for f in still_open:
            if f.id not in observed_finding_ids:
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
    return scan, history, imported_ownership_rules, imported_exceptions
