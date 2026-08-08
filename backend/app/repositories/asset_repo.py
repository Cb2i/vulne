from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import Asset


def get_or_create_asset(db: Session, *, hostname: str, defaults: dict) -> Asset:
    asset = db.scalar(select(Asset).where(Asset.hostname == hostname))
    if asset is None:
        asset = Asset(hostname=hostname, **defaults)
        db.add(asset)
        # A new asset's id isn't assigned until it's actually inserted, and callers
        # generally need it right away (e.g. to key it into a dict) -- but an existing,
        # already-persistent asset needs no flush just to update its in-memory attributes.
        db.flush()
        return asset
    for key, value in defaults.items():
        if value not in (None, ""):
            setattr(asset, key, value)
    return asset
