"""Orchestrates the CAA / SLE / ownership / exception engines against a single Finding,
so both the importer and the "recompute" API endpoint share one code path."""
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.enums import FindingStatus
from app.models.finding import Finding
from app.repositories.rules_repo import (
    get_active_caa_config,
    list_active_exceptions,
    list_active_ownership_rules,
    list_sle_rules,
)
from app.rules.caa.engine import compute_caa_score
from app.rules.exceptions.engine import find_matching_exception
from app.rules.ownership.engine import resolve_team
from app.rules.sle.engine import resolve_sle


def score_finding(db: Session, finding: Finding, asset: Asset, *, as_of: date | None = None) -> Finding:
    """Recompute CAA score, SLE due date, team ownership, and exception status for one finding."""
    caa_config = get_active_caa_config(db)
    sle_rules = list_sle_rules(db)
    ownership_rules = list_active_ownership_rules(db)
    exceptions = list_active_exceptions(db)

    if asset.is_decommissioned:
        finding.status = FindingStatus.DECOMMISSIONED
        return finding

    caa_result = compute_caa_score(
        cvss=finding.cvss,
        exposition=asset.exposition,
        criticite=asset.criticite,
        exploitable=finding.exploitable,
        config=caa_config,
    )
    finding.caa_score = caa_result.caa_score

    sle_result = resolve_sle(caa_result.caa_score, sle_rules, from_date=finding.first_seen_at.date())
    finding.caa_severity = sle_result.severity
    finding.sle_delay_days = sle_result.delay_days
    finding.sle_due_date = sle_result.due_date

    team_id = resolve_team(hostname=asset.hostname, os=asset.os, rules=ownership_rules)
    finding.team_id = team_id
    if asset.team_id is None and team_id is not None:
        asset.team_id = team_id

    matched_exception = find_matching_exception(
        plugin_name=finding.plugin_name,
        cve=finding.cve,
        hostname=asset.hostname,
        exceptions=exceptions,
        today=as_of,
    )
    if matched_exception:
        finding.exception_id = matched_exception.id
        if finding.status == FindingStatus.OPEN:
            finding.status = FindingStatus.EXCEPTION
    else:
        finding.exception_id = None
        if finding.status == FindingStatus.EXCEPTION:
            finding.status = FindingStatus.OPEN

    return finding


def recompute_all_open_findings(db: Session) -> int:
    """Re-run scoring for every non-resolved finding. Used after rule changes."""
    from sqlalchemy import select

    findings = db.scalars(
        select(Finding).where(Finding.status.in_([FindingStatus.OPEN, FindingStatus.EXCEPTION]))
    ).all()
    count = 0
    for finding in findings:
        asset = db.get(Asset, finding.asset_id)
        if asset is None:
            continue
        score_finding(db, finding, asset)
        count += 1
    db.commit()
    return count
