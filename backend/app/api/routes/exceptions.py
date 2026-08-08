from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.exception import ExceptionRecord
from app.models.user import User
from app.schemas.exception import ExceptionCreate, ExceptionRead, ExceptionUpdate
from app.services.scoring_service import recompute_all_open_findings

router = APIRouter(prefix="/api/exceptions", tags=["exceptions"])


@router.get("", response_model=list[ExceptionRead], dependencies=[Depends(get_current_user)])
def list_exceptions(db: Session = Depends(get_db)) -> list[ExceptionRecord]:
    return list(db.scalars(select(ExceptionRecord).order_by(ExceptionRecord.granted_at.desc())))


@router.post("", response_model=ExceptionRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_exception(
    payload: ExceptionCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)
) -> ExceptionRecord:
    exc = ExceptionRecord(**payload.model_dump(), created_by_id=current_user.id)
    db.add(exc)
    db.commit()
    db.refresh(exc)
    recompute_all_open_findings(db)
    return exc


@router.patch("/{exception_id}", response_model=ExceptionRead, dependencies=[Depends(require_admin)])
def update_exception(exception_id: int, payload: ExceptionUpdate, db: Session = Depends(get_db)) -> ExceptionRecord:
    exc = db.get(ExceptionRecord, exception_id)
    if not exc:
        raise HTTPException(status_code=404, detail="Exception introuvable")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(exc, key, value)
    db.commit()
    db.refresh(exc)
    recompute_all_open_findings(db)
    return exc


@router.delete("/{exception_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_exception(exception_id: int, db: Session = Depends(get_db)) -> None:
    exc = db.get(ExceptionRecord, exception_id)
    if not exc:
        raise HTTPException(status_code=404, detail="Exception introuvable")
    db.delete(exc)
    db.commit()
    recompute_all_open_findings(db)
