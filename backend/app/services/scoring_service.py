"""Orchestrates the CAA / SLE / ownership / exception engines against Findings, so both
the importer and the "recompute" API endpoints share one code path.

Loading the active CAA config, SLE rules, ownership rules and active exceptions is
factored into ScoringContext and done *once* per batch (import, asset rescore, or full
recompute) rather than per finding -- with several thousand findings, reloading those
four queries inside a per-finding loop turned a single-digit-second operation into a
30-90 second one, which is exactly what made rule edits and large imports look hung.
"""
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.enums import FindingStatus
from app.models.exception import ExceptionRecord
from app.models.finding import Finding
from app.models.rules import CAAConfig, OwnershipRule, SLERule
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


@dataclass
class ScoringContext:
    caa_config: CAAConfig
    sle_rules: list[SLERule]
    ownership_rules: list[OwnershipRule]
    exceptions: list[ExceptionRecord]


def load_scoring_context(db: Session) -> ScoringContext:
    return ScoringContext(
        caa_config=get_active_caa_config(db),
        sle_rules=list_sle_rules(db),
        ownership_rules=list_active_ownership_rules(db),
        exceptions=list_active_exceptions(db),
    )


def score_finding(
    finding: Finding, asset: Asset, context: ScoringContext, *, as_of: date | None = None
) -> Finding:
    """Recompute CAA score, SLE due date, team ownership, and exception status for one
    finding, using an already-loaded ScoringContext (see load_scoring_context)."""
    if asset.is_decommissioned:
        finding.status = FindingStatus.DECOMMISSIONED
        return finding

    caa_result = compute_caa_score(
        cvss=finding.cvss,
        exposition=asset.exposition,
        criticite=asset.criticite,
        exploitable=finding.exploitable,
        config=context.caa_config,
    )
    finding.caa_score = caa_result.caa_score

    sle_result = resolve_sle(caa_result.caa_score, context.sle_rules, from_date=finding.first_seen_at.date())
    finding.caa_severity = sle_result.severity
    finding.sle_delay_days = sle_result.delay_days
    finding.sle_due_date = sle_result.due_date

    # A team already set on the asset (whether from a prior rule match or a manual
    # override via the Assets page) takes precedence; only fall back to the ownership
    # rules — and cache their result onto the asset — when it has no team yet.
    if asset.team_id is not None:
        team_id = asset.team_id
    else:
        team_id = resolve_team(hostname=asset.hostname, os=asset.os, rules=context.ownership_rules)
        if team_id is not None:
            asset.team_id = team_id
    finding.team_id = team_id

    matched_exception = find_matching_exception(
        plugin_name=finding.plugin_name,
        cve=finding.cve,
        hostname=asset.hostname,
        exceptions=context.exceptions,
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


def rescore_asset_findings(db: Session, asset: Asset) -> int:
    """Re-run scoring for one asset's open findings. Used after an asset's exposure,
    criticité, or team is edited directly (those inputs feed the CAA/ownership engines)."""
    context = load_scoring_context(db)
    findings = db.scalars(
        select(Finding).where(
            Finding.asset_id == asset.id,
            Finding.status.in_([FindingStatus.OPEN, FindingStatus.EXCEPTION]),
        )
    ).all()
    for finding in findings:
        score_finding(finding, asset, context)
    return len(findings)


def recompute_all_open_findings(db: Session) -> int:
    """Re-run scoring for every non-resolved finding. Used after rule changes."""
    context = load_scoring_context(db)
    findings = db.scalars(
        select(Finding).where(Finding.status.in_([FindingStatus.OPEN, FindingStatus.EXCEPTION]))
    ).all()
    if not findings:
        return 0

    asset_ids = {f.asset_id for f in findings}
    assets_by_id = {a.id: a for a in db.scalars(select(Asset).where(Asset.id.in_(asset_ids)))}

    count = 0
    for finding in findings:
        asset = assets_by_id.get(finding.asset_id)
        if asset is None:
            continue
        score_finding(finding, asset, context)
        count += 1
    db.commit()
    return count
