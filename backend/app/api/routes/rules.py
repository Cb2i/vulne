from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.rules import CAAConfig, OwnershipRule, SLERule
from app.schemas.rules import (
    CAAConfigRead,
    CAAConfigUpdate,
    OwnershipRuleCreate,
    OwnershipRuleRead,
    OwnershipRuleUpdate,
    SLERuleRead,
    SLERuleUpdate,
)
from app.services.scoring_service import recompute_all_open_findings

router = APIRouter(prefix="/api/rules", tags=["rules"])


# ── CAA config ────────────────────────────────────────────────────────────
@router.get("/caa", response_model=CAAConfigRead, dependencies=[Depends(get_current_user)])
def get_caa_config(db: Session = Depends(get_db)) -> CAAConfig:
    config = db.scalar(select(CAAConfig).where(CAAConfig.is_active.is_(True)))
    if not config:
        raise HTTPException(status_code=404, detail="Aucune configuration CAA active")
    return config


@router.patch("/caa", response_model=CAAConfigRead, dependencies=[Depends(require_admin)])
def update_caa_config(payload: CAAConfigUpdate, db: Session = Depends(get_db)) -> CAAConfig:
    config = db.scalar(select(CAAConfig).where(CAAConfig.is_active.is_(True)))
    if not config:
        raise HTTPException(status_code=404, detail="Aucune configuration CAA active")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(config, key, value)
    db.commit()
    db.refresh(config)
    recompute_all_open_findings(db)
    return config


# ── SLE rules ─────────────────────────────────────────────────────────────
@router.get("/sle", response_model=list[SLERuleRead], dependencies=[Depends(get_current_user)])
def list_sle_rules(db: Session = Depends(get_db)) -> list[SLERule]:
    return list(db.scalars(select(SLERule).order_by(SLERule.caa_min.desc())))


@router.patch("/sle/{rule_id}", response_model=SLERuleRead, dependencies=[Depends(require_admin)])
def update_sle_rule(rule_id: int, payload: SLERuleUpdate, db: Session = Depends(get_db)) -> SLERule:
    rule = db.get(SLERule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Règle SLE introuvable")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    recompute_all_open_findings(db)
    return rule


# ── Ownership rules ───────────────────────────────────────────────────────
@router.get("/ownership", response_model=list[OwnershipRuleRead], dependencies=[Depends(get_current_user)])
def list_ownership_rules(db: Session = Depends(get_db)) -> list[OwnershipRule]:
    return list(db.scalars(select(OwnershipRule).order_by(OwnershipRule.priority)))


@router.post(
    "/ownership",
    response_model=OwnershipRuleRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_ownership_rule(payload: OwnershipRuleCreate, db: Session = Depends(get_db)) -> OwnershipRule:
    rule = OwnershipRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    recompute_all_open_findings(db)
    return rule


@router.patch("/ownership/{rule_id}", response_model=OwnershipRuleRead, dependencies=[Depends(require_admin)])
def update_ownership_rule(rule_id: int, payload: OwnershipRuleUpdate, db: Session = Depends(get_db)) -> OwnershipRule:
    rule = db.get(OwnershipRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Règle de propriété introuvable")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    recompute_all_open_findings(db)
    return rule


@router.delete("/ownership/{rule_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_ownership_rule(rule_id: int, db: Session = Depends(get_db)) -> None:
    rule = db.get(OwnershipRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Règle de propriété introuvable")
    db.delete(rule)
    db.commit()
    recompute_all_open_findings(db)
