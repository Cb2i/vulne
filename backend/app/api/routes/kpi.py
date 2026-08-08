from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.kpi import KPISummary
from app.services.kpi_service import get_kpi_summary

router = APIRouter(prefix="/api/kpi", tags=["kpi"])


@router.get("/summary", response_model=KPISummary)
def kpi_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> KPISummary:
    if current_user.role == UserRole.TEAM_MANAGER:
        # A team manager with no team assigned must see nothing, not the global summary.
        # -1 is not a valid team id, so every team_id-scoped query below matches zero rows.
        team_id = current_user.team_id or -1
    else:
        team_id = None
    return get_kpi_summary(db, team_id=team_id)
