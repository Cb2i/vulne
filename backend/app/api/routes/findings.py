from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import false, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_analyst_or_admin
from app.models.asset import Asset
from app.models.enums import FindingStatus, Severity, UserRole
from app.models.finding import Finding
from app.models.team import Team
from app.models.user import User
from app.schemas.finding import FindingListResponse, FindingRead, FindingUpdate

router = APIRouter(prefix="/api/findings", tags=["findings"])


def _scope_to_team(query, current_user: User):
    """Team managers only see their team's findings. A team manager with no team
    assigned gets an empty result set rather than falling through to global access."""
    if current_user.role == UserRole.TEAM_MANAGER:
        if not current_user.team_id:
            return query.where(false())
        query = query.where(Finding.team_id == current_user.team_id)
    return query


def _enrich(db: Session, findings: list[Finding]) -> list[FindingRead]:
    asset_ids = {f.asset_id for f in findings}
    team_ids = {f.team_id for f in findings if f.team_id}
    assets = {a.id: a for a in db.scalars(select(Asset).where(Asset.id.in_(asset_ids)))} if asset_ids else {}
    teams = {t.id: t for t in db.scalars(select(Team).where(Team.id.in_(team_ids)))} if team_ids else {}

    results = []
    for f in findings:
        item = FindingRead.model_validate(f)
        asset = assets.get(f.asset_id)
        item.hostname = asset.hostname if asset else None
        team = teams.get(f.team_id) if f.team_id else None
        item.team_name = team.name if team else None
        results.append(item)
    return results


@router.get("", response_model=FindingListResponse)
def list_findings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status_filter: FindingStatus | None = Query(None, alias="status"),
    severity: Severity | None = None,
    team_id: int | None = None,
    hostname: str | None = None,
    search: str | None = None,
    overdue_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> FindingListResponse:
    from datetime import date

    query = select(Finding)
    query = _scope_to_team(query, current_user)

    if status_filter:
        query = query.where(Finding.status == status_filter)
    if severity:
        query = query.where(Finding.caa_severity == severity)
    if team_id:
        query = query.where(Finding.team_id == team_id)
    if overdue_only:
        query = query.where(Finding.sle_due_date < date.today())
    if hostname:
        query = query.join(Asset).where(Asset.hostname.ilike(f"%{hostname}%"))
    if search:
        like = f"%{search}%"
        query = query.where((Finding.plugin_name.ilike(like)) | (Finding.cve.ilike(like)))

    total = len(list(db.scalars(query)))
    query = query.order_by(Finding.caa_score.desc().nullslast()).offset((page - 1) * page_size).limit(page_size)
    findings = list(db.scalars(query))

    return FindingListResponse(total=total, page=page, page_size=page_size, items=_enrich(db, findings))


@router.get("/{finding_id}", response_model=FindingRead)
def get_finding(finding_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> FindingRead:
    finding = db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding introuvable")
    if current_user.role == UserRole.TEAM_MANAGER and (
        not current_user.team_id or finding.team_id != current_user.team_id
    ):
        raise HTTPException(status_code=403, detail="Accès refusé à ce finding")
    return _enrich(db, [finding])[0]


@router.patch("/{finding_id}", response_model=FindingRead, dependencies=[Depends(require_analyst_or_admin)])
def update_finding(finding_id: int, payload: FindingUpdate, db: Session = Depends(get_db)) -> FindingRead:
    finding = db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding introuvable")
    from datetime import datetime, timezone

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(finding, key, value)
    if data.get("status") == FindingStatus.REMEDIATED and finding.resolved_at is None:
        finding.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(finding)
    return _enrich(db, [finding])[0]
