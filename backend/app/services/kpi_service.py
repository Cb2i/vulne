from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.enums import FindingStatus
from app.models.exception import ExceptionRecord
from app.models.finding import Finding
from app.models.team import Team
from app.schemas.kpi import KPISummary, SeverityCount, TeamCount


def get_kpi_summary(db: Session, *, team_id: int | None = None) -> KPISummary:
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)

    open_statuses = [FindingStatus.OPEN, FindingStatus.EXCEPTION]

    base_query = select(Finding).where(Finding.status.in_(open_statuses))
    if team_id is not None:
        base_query = base_query.where(Finding.team_id == team_id)
    open_findings = list(db.scalars(base_query))

    total_open = len(open_findings)
    overdue = sum(1 for f in open_findings if f.sle_due_date and f.sle_due_date < today)
    compliance_rate = round(100.0 * (total_open - overdue) / total_open, 1) if total_open else 100.0

    by_severity: dict[str, int] = {}
    for f in open_findings:
        key = f.caa_severity.value if f.caa_severity else "Non évalué"
        by_severity[key] = by_severity.get(key, 0) + 1

    team_names = {t.id: t.name for t in db.scalars(select(Team))}
    by_team: dict[int | None, dict[str, int]] = {}
    for f in open_findings:
        bucket = by_team.setdefault(f.team_id, {"count": 0, "overdue": 0})
        bucket["count"] += 1
        if f.sle_due_date and f.sle_due_date < today:
            bucket["overdue"] += 1

    total_assets = db.scalar(select(func.count()).select_from(Asset)) or 0
    total_decommissioned = db.scalar(select(func.count()).select_from(Asset).where(Asset.is_decommissioned.is_(True))) or 0
    active_exceptions = db.scalar(select(func.count()).select_from(ExceptionRecord).where(ExceptionRecord.status == "active")) or 0

    remediated_30d = db.scalar(
        select(func.count()).select_from(Finding).where(
            Finding.status == FindingStatus.REMEDIATED,
            Finding.resolved_at.is_not(None),
            Finding.resolved_at >= thirty_days_ago,
        )
    ) or 0
    new_30d = db.scalar(
        select(func.count()).select_from(Finding).where(Finding.first_seen_at >= thirty_days_ago)
    ) or 0

    return KPISummary(
        total_open_findings=total_open,
        total_assets=total_assets,
        total_decommissioned_assets=total_decommissioned,
        active_exceptions=active_exceptions,
        overdue_findings=overdue,
        sle_compliance_rate=compliance_rate,
        by_severity=[SeverityCount(severity=k, count=v) for k, v in sorted(by_severity.items())],
        by_team=[
            TeamCount(
                team_id=tid,
                team_name=team_names.get(tid, "Non assigné") if tid else "Non assigné",
                count=v["count"],
                overdue_count=v["overdue"],
            )
            for tid, v in sorted(by_team.items(), key=lambda kv: kv[1]["count"], reverse=True)
        ],
        remediated_last_30_days=remediated_30d,
        new_last_30_days=new_30d,
    )
