from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin, require_analyst_or_admin
from app.importers.tenable_excel.parser import TenableImportError
from app.models.scan import Scan
from app.models.user import User
from app.schemas.scan import ImportResult, ScanComparisonResult, ScanRead
from app.services.import_service import import_tenable_workbook
from app.services.scan_comparison_service import compare_scans
from app.services.scan_service import delete_scan

router = APIRouter(prefix="/api/scans", tags=["scans"])


@router.get("", response_model=list[ScanRead], dependencies=[Depends(get_current_user)])
def list_scans(db: Session = Depends(get_db)) -> list[Scan]:
    return list(db.scalars(select(Scan).order_by(Scan.imported_at.desc())))


@router.post("/import", response_model=ImportResult, dependencies=[Depends(require_analyst_or_admin)])
async def import_scan(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst_or_admin),
) -> ImportResult:
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=400, detail="Le fichier doit être un classeur Excel (.xlsx)")

    content = await file.read()
    try:
        scan, history, imported_ownership_rules, imported_exceptions = import_tenable_workbook(
            db, file_bytes=content, filename=file.filename, imported_by_id=current_user.id
        )
    except TenableImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ImportResult(
        scan_id=scan.id,
        scan_name=scan.name,
        row_count=history.row_count,
        new_findings=history.new_findings,
        updated_findings=history.updated_findings,
        resolved_findings=history.resolved_findings,
        imported_ownership_rules=imported_ownership_rules,
        imported_exceptions=imported_exceptions,
        status=history.status,
        warnings=history.error_details.split("; ") if history.error_details else [],
    )


@router.get("/compare", response_model=ScanComparisonResult, dependencies=[Depends(get_current_user)])
def compare(baseline_scan_id: int, current_scan_id: int, db: Session = Depends(get_db)) -> ScanComparisonResult:
    if not db.get(Scan, baseline_scan_id) or not db.get(Scan, current_scan_id):
        raise HTTPException(status_code=404, detail="Scan introuvable")
    return compare_scans(db, baseline_scan_id, current_scan_id)


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_scan_endpoint(scan_id: int, db: Session = Depends(get_db)) -> None:
    """Deletes an imported scan. Findings still observed by other scans are kept and
    re-anchored; findings only ever seen in this scan are removed with it. Exceptions
    and ownership rules imported alongside it are never touched by this."""
    if not db.get(Scan, scan_id):
        raise HTTPException(status_code=404, detail="Scan introuvable")
    delete_scan(db, scan_id)
