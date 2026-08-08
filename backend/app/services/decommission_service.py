from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.decommission import Decommission
from app.models.enums import FindingStatus
from app.models.finding import Finding


def decommission_asset(
    db: Session,
    *,
    hostname: str,
    reason: str | None,
    decommissioned_at: date | None,
    decommissioned_by_id: int | None,
) -> Decommission:
    asset = db.scalar(select(Asset).where(Asset.hostname == hostname))
    if asset:
        asset.is_decommissioned = True

    record = Decommission(
        asset_id=asset.id if asset else None,
        hostname=hostname,
        decommissioned_at=decommissioned_at or date.today(),
        reason=reason,
        decommissioned_by_id=decommissioned_by_id,
    )
    db.add(record)

    if asset:
        open_findings = db.scalars(
            select(Finding).where(
                Finding.asset_id == asset.id,
                Finding.status.in_([FindingStatus.OPEN, FindingStatus.EXCEPTION]),
            )
        )
        for finding in open_findings:
            finding.status = FindingStatus.DECOMMISSIONED

    db.commit()
    db.refresh(record)
    return record
