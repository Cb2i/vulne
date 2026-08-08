from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_analyst_or_admin
from app.exporters.excel_exporter import export_findings_to_excel, export_kpi_to_excel
from app.models.enums import FindingStatus, Severity
from app.models.finding import Finding
from app.services.kpi_service import get_kpi_summary

router = APIRouter(prefix="/api/exports", tags=["exports"], dependencies=[Depends(require_analyst_or_admin)])


def _xlsx_response(content: bytes, filename: str) -> StreamingResponse:
    return StreamingResponse(
        iter([content]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/findings")
def export_findings(
    db: Session = Depends(get_db),
    status_filter: FindingStatus | None = Query(None, alias="status"),
    severity: Severity | None = None,
    team_id: int | None = None,
) -> StreamingResponse:
    query = select(Finding)
    if status_filter:
        query = query.where(Finding.status == status_filter)
    if severity:
        query = query.where(Finding.caa_severity == severity)
    if team_id:
        query = query.where(Finding.team_id == team_id)
    findings = list(db.scalars(query))
    content = export_findings_to_excel(db, findings)
    filename = f"vulnassist_findings_{date.today().isoformat()}.xlsx"
    return _xlsx_response(content, filename)


@router.get("/kpi")
def export_kpi(db: Session = Depends(get_db)) -> StreamingResponse:
    summary = get_kpi_summary(db)
    content = export_kpi_to_excel(summary)
    filename = f"vulnassist_kpi_{date.today().isoformat()}.xlsx"
    return _xlsx_response(content, filename)
