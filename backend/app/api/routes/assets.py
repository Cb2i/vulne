from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_analyst_or_admin
from app.models.asset import Asset
from app.schemas.asset import AssetRead, AssetUpdate

router = APIRouter(prefix="/api/assets", tags=["assets"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[AssetRead])
def list_assets(
    db: Session = Depends(get_db),
    search: str | None = None,
    team_id: int | None = None,
    include_decommissioned: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
) -> list[Asset]:
    query = select(Asset)
    if not include_decommissioned:
        query = query.where(Asset.is_decommissioned.is_(False))
    if team_id:
        query = query.where(Asset.team_id == team_id)
    if search:
        like = f"%{search}%"
        query = query.where(Asset.hostname.ilike(like))
    query = query.order_by(Asset.hostname).offset((page - 1) * page_size).limit(page_size)
    return list(db.scalars(query))


@router.patch("/{asset_id}", response_model=AssetRead, dependencies=[Depends(require_analyst_or_admin)])
def update_asset(asset_id: int, payload: AssetUpdate, db: Session = Depends(get_db)) -> Asset:
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Actif introuvable")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(asset, key, value)
    db.commit()
    db.refresh(asset)
    return asset
