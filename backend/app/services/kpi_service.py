from datetime import date, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.enums import FindingStatus
from app.models.exception import ExceptionRecord
from app.models.finding import Finding
from app.models.team import Team
from app.schemas.kpi import KPISummary, SeverityCount, TeamCount


def get_kpi_summary(db: Session, *, team_id: int | None = None) -> KPISummary:
    """All aggregation happens in SQL (COUNT/GROUP BY) rather than loading every open
    finding into Python -- with tens of thousands of findings, hydrating full ORM
    objects just to sum/group them in a for-loop made every dashboard load noticeably
    slow, since this endpoint is hit on essentially every visit to the app."""
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)

    open_statuses = [FindingStatus.OPEN, FindingStatus.EXCEPTION]
    overdue_case = case((Finding.sle_due_date < today, 1), else_=0)

    open_filter = [Finding.status.in_(open_statuses)]
    if team_id is not None:
        open_filter.append(Finding.team_id == team_id)

    total_open, overdue = db.execute(
        select(func.count(), func.coalesce(func.sum(overdue_case), 0)).where(*open_filter)
    ).one()
    compliance_rate = round(100.0 * (total_open - overdue) / total_open, 1) if total_open else 100.0

    severity_rows = db.execute(
        select(Finding.caa_severity, func.count()).where(*open_filter).group_by(Finding.caa_severity)
    ).all()
    by_severity = {(sev.value if sev else "Non évalué"): count for sev, count in severity_rows}

    team_rows = db.execute(
        select(Finding.team_id, func.count(), func.coalesce(func.sum(overdue_case), 0))
        .where(*open_filter)
        .group_by(Finding.team_id)
    ).all()
    team_names = {t.id: t.name for t in db.scalars(select(Team))}

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
                count=count,
                overdue_count=overdue_count,
            )
            for tid, count, overdue_count in sorted(team_rows, key=lambda row: row[1], reverse=True)
        ],
        remediated_last_30_days=remediated_30d,
        new_last_30_days=new_30d,
    )
