from pydantic import BaseModel


class SeverityCount(BaseModel):
    severity: str
    count: int


class TeamCount(BaseModel):
    team_id: int | None
    team_name: str
    count: int
    overdue_count: int


class KPISummary(BaseModel):
    total_open_findings: int
    total_assets: int
    total_decommissioned_assets: int
    active_exceptions: int
    overdue_findings: int
    sle_compliance_rate: float
    by_severity: list[SeverityCount]
    by_team: list[TeamCount]
    remediated_last_30_days: int
    new_last_30_days: int
