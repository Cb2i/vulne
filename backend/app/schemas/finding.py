from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import FindingStatus, Severity


class FindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scan_id: int
    asset_id: int
    plugin_name: str
    cve: str | None = None
    grade: str | None = None
    score: float | None = None
    protocol: str | None = None
    port: int | None = None
    description: str | None = None
    solution: str | None = None
    cvss_version: str | None = None
    cvss: float | None = None
    exploitable: bool

    caa_score: float | None = None
    caa_severity: Severity | None = None
    sle_delay_days: int | None = None
    sle_due_date: date | None = None
    team_id: int | None = None

    status: FindingStatus
    remediation_comment: str | None = None
    ticket_ref: str | None = None
    exception_id: int | None = None

    first_seen_at: datetime
    last_seen_at: datetime
    resolved_at: datetime | None = None

    # Denormalized convenience fields, populated by the API layer.
    hostname: str | None = None
    team_name: str | None = None


class FindingUpdate(BaseModel):
    status: FindingStatus | None = None
    remediation_comment: str | None = None
    ticket_ref: str | None = None
    team_id: int | None = None


class FindingListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[FindingRead]
