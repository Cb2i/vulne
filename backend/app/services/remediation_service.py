from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import FindingStatus
from app.models.finding import Finding
from app.models.remediation import RemediationAction, RemediationActionFinding
from app.rules.remediation.engine import group_findings_for_remediation


def preview_remediation_groups(db: Session, *, team_id: int | None = None) -> list:
    query = select(Finding).where(Finding.status.in_([FindingStatus.OPEN, FindingStatus.EXCEPTION]))
    if team_id is not None:
        query = query.where(Finding.team_id == team_id)
    findings = list(db.scalars(query))
    return group_findings_for_remediation(findings)


def create_remediation_action_from_group(
    db: Session, *, plugin_name: str, finding_ids: list[int], created_by_id: int | None
) -> RemediationAction:
    findings = list(db.scalars(select(Finding).where(Finding.id.in_(finding_ids))))
    if not findings:
        raise ValueError("No findings match the provided ids")

    team_ids = {f.team_id for f in findings if f.team_id}
    action = RemediationAction(
        title=f"Remédiation groupée — {plugin_name}",
        plugin_name=plugin_name,
        solution=findings[0].solution,
        team_id=next(iter(team_ids)) if len(team_ids) == 1 else None,
        finding_count=len(findings),
        created_by_id=created_by_id,
    )
    db.add(action)
    db.flush()

    for f in findings:
        db.add(RemediationActionFinding(action_id=action.id, finding_id=f.id))

    db.commit()
    db.refresh(action)
    return action
