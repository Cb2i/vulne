from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import Asset


def get_or_create_asset(db: Session, *, hostname: str, defaults: dict) -> Asset:
    asset = db.scalar(select(Asset).where(Asset.hostname == hostname))
    if asset is None:
        asset = Asset(hostname=hostname, **defaults)
        db.add(asset)
        db.flush()
        return asset
    for key, value in defaults.items():
        if value not in (None, ""):
            setattr(asset, key, value)
    db.flush()
    return asset
