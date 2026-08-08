from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ImportStatus


class ScanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    source_filename: str | None = None
    imported_at: datetime
    finding_count: int
    status: ImportStatus


class ImportResult(BaseModel):
    scan_id: int
    scan_name: str
    row_count: int
    new_findings: int
    updated_findings: int
    resolved_findings: int
    imported_ownership_rules: int = 0
    imported_exceptions: int = 0
    status: ImportStatus
    warnings: list[str] = []


class ScanComparisonResult(BaseModel):
    baseline_scan_id: int
    current_scan_id: int
    new_finding_ids: list[int]
    resolved_finding_ids: list[int]
    persisting_finding_ids: list[int]
    new_count: int
    resolved_count: int
    persisting_count: int
