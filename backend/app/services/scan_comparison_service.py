"""Compares two scans (by finding identity = asset + plugin_name + port) to compute
which findings are new, resolved (fixed) or persisting between them."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.finding import Finding
from app.schemas.scan import ScanComparisonResult


def _identity(f: Finding) -> tuple:
    return (f.asset_id, f.plugin_name, f.port)


def compare_scans(db: Session, baseline_scan_id: int, current_scan_id: int) -> ScanComparisonResult:
    baseline = list(db.scalars(select(Finding).where(Finding.scan_id == baseline_scan_id)))
    current = list(db.scalars(select(Finding).where(Finding.scan_id == current_scan_id)))

    baseline_by_identity = {_identity(f): f for f in baseline}
    current_by_identity = {_identity(f): f for f in current}

    new_ids = [f.id for key, f in current_by_identity.items() if key not in baseline_by_identity]
    resolved_ids = [f.id for key, f in baseline_by_identity.items() if key not in current_by_identity]
    persisting_ids = [f.id for key, f in current_by_identity.items() if key in baseline_by_identity]

    return ScanComparisonResult(
        baseline_scan_id=baseline_scan_id,
        current_scan_id=current_scan_id,
        new_finding_ids=new_ids,
        resolved_finding_ids=resolved_ids,
        persisting_finding_ids=persisting_ids,
        new_count=len(new_ids),
        resolved_count=len(resolved_ids),
        persisting_count=len(persisting_ids),
    )
