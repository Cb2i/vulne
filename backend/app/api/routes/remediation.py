from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_analyst_or_admin
from app.models.remediation import RemediationAction
from app.models.user import User
from app.schemas.remediation import RemediationActionRead, RemediationActionUpdate, RemediationGroupPreview
from app.services.remediation_service import create_remediation_action_from_group, preview_remediation_groups

router = APIRouter(prefix="/api/remediation", tags=["remediation"])


@router.get("/groups", response_model=list[RemediationGroupPreview], dependencies=[Depends(get_current_user)])
def get_remediation_groups(db: Session = Depends(get_db), team_id: int | None = None) -> list[RemediationGroupPreview]:
    groups = preview_remediation_groups(db, team_id=team_id)
    return [
        RemediationGroupPreview(
            plugin_name=g.plugin_name,
            solution=g.solution,
            finding_count=len(g.finding_ids),
            asset_count=len(g.asset_ids),
            team_ids=list(g.team_ids),
            max_caa_score=g.max_caa_score,
            finding_ids=g.finding_ids,
        )
        for g in groups
    ]


@router.get("/actions", response_model=list[RemediationActionRead], dependencies=[Depends(get_current_user)])
def list_actions(db: Session = Depends(get_db)) -> list[RemediationAction]:
    return list(db.scalars(select(RemediationAction).order_by(RemediationAction.created_at.desc())))


@router.post("/actions", response_model=RemediationActionRead, dependencies=[Depends(require_analyst_or_admin)])
def create_action(
    plugin_name: str = Body(...),
    finding_ids: list[int] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst_or_admin),
) -> RemediationAction:
    try:
        return create_remediation_action_from_group(
            db, plugin_name=plugin_name, finding_ids=finding_ids, created_by_id=current_user.id
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/actions/{action_id}", response_model=RemediationActionRead, dependencies=[Depends(require_analyst_or_admin)])
def update_action(action_id: int, payload: RemediationActionUpdate, db: Session = Depends(get_db)) -> RemediationAction:
    action = db.get(RemediationAction, action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action de remédiation introuvable")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(action, key, value)
    db.commit()
    db.refresh(action)
    return action
