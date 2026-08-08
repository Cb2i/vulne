"""Deleting a scan/import. This is destructive and admin-only, so it's handled
carefully: a finding is only ever hard-deleted if the scan being removed was the
*only* scan that ever observed it (via ScanObservation); a finding still observed in
other scans is kept and re-anchored to the oldest scan that still observed it, so
currently-relevant vulnerability data is never lost just because one import is undone.

Everything here is done as bulk statements over ids rather than looping per finding
with per-row queries -- with tens of thousands of findings in a scan, a naive
per-finding loop turned "delete this import" into an operation that never returned.
"""
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.models.finding import Finding
from app.models.import_history import ImportHistory
from app.models.remediation import RemediationActionFinding
from app.models.scan import Scan
from app.models.scan_observation import ScanObservation


def delete_scan(db: Session, scan_id: int) -> None:
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise ValueError("Scan introuvable")

    finding_ids = list(db.scalars(select(Finding.id).where(Finding.scan_id == scan_id)))

    if finding_ids:
        # For every finding in this scan, is it also observed under some OTHER scan?
        # One bulk query, picking the earliest other observation per finding in
        # Python, instead of one query per finding.
        other_observations = db.execute(
            select(ScanObservation.finding_id, ScanObservation.scan_id, ScanObservation.observed_at)
            .where(ScanObservation.finding_id.in_(finding_ids), ScanObservation.scan_id != scan_id)
            .order_by(ScanObservation.finding_id, ScanObservation.observed_at.asc())
        ).all()
        earliest_other_scan: dict[int, int] = {}
        for finding_id, other_scan_id, _observed_at in other_observations:
            earliest_other_scan.setdefault(finding_id, other_scan_id)

        delete_ids = [fid for fid in finding_ids if fid not in earliest_other_scan]

        # Group the "keep" findings by their new target scan, so each group can be
        # re-anchored with a single bulk UPDATE instead of one per finding.
        by_target_scan: dict[int, list[int]] = {}
        for fid, target_scan_id in earliest_other_scan.items():
            by_target_scan.setdefault(target_scan_id, []).append(fid)
        for target_scan_id, ids in by_target_scan.items():
            db.execute(update(Finding).where(Finding.id.in_(ids)).values(scan_id=target_scan_id))

        if delete_ids:
            db.execute(delete(RemediationActionFinding).where(RemediationActionFinding.finding_id.in_(delete_ids)))
            db.execute(delete(Finding).where(Finding.id.in_(delete_ids)))

    db.execute(delete(ScanObservation).where(ScanObservation.scan_id == scan_id))

    # Preserve the audit trail (an import happened on this date, produced N rows) but
    # detach it from the scan being deleted, rather than erasing the history entirely.
    db.execute(update(ImportHistory).where(ImportHistory.scan_id == scan_id).values(scan_id=None))

    db.delete(scan)
    db.commit()
