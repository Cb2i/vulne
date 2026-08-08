from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.decommission import Decommission
from app.models.user import User
from app.schemas.decommission import DecommissionCreate, DecommissionRead
from app.services.decommission_service import decommission_asset

router = APIRouter(prefix="/api/decommission", tags=["decommission"])


@router.get("", response_model=list[DecommissionRead], dependencies=[Depends(get_current_user)])
def list_decommissioned(db: Session = Depends(get_db)) -> list[Decommission]:
    return list(db.scalars(select(Decommission).order_by(Decommission.decommissioned_at.desc())))


@router.post("", response_model=DecommissionRead, dependencies=[Depends(require_admin)])
def create_decommission(
    payload: DecommissionCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)
) -> Decommission:
    return decommission_asset(
        db,
        hostname=payload.hostname,
        reason=payload.reason,
        decommissioned_at=payload.decommissioned_at,
        decommissioned_by_id=current_user.id,
    )
