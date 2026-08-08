"""Compares two scans by their recorded ScanObservation membership to compute which
findings are new, resolved (fixed), or persisting between them.

Findings are deduplicated across imports (the same vulnerability instance is one Finding
row that can be observed by many scans over time), so comparing on Finding.scan_id would
only reflect the scan that last touched a finding, not the scans it actually appeared in.
ScanObservation rows are written once per (scan, finding) pair and never mutated, which is
what makes this comparison accurate regardless of how many imports happened in between.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.scan_observation import ScanObservation
from app.schemas.scan import ScanComparisonResult


def compare_scans(db: Session, baseline_scan_id: int, current_scan_id: int) -> ScanComparisonResult:
    baseline_ids = set(
        db.scalars(select(ScanObservation.finding_id).where(ScanObservation.scan_id == baseline_scan_id))
    )
    current_ids = set(
        db.scalars(select(ScanObservation.finding_id).where(ScanObservation.scan_id == current_scan_id))
    )

    new_ids = sorted(current_ids - baseline_ids)
    resolved_ids = sorted(baseline_ids - current_ids)
    persisting_ids = sorted(current_ids & baseline_ids)

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
