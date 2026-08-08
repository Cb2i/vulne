from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RemediationActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    plugin_name: str
    solution: str | None = None
    team_id: int | None = None
    ticket_ref: str | None = None
    status: str
    finding_count: int
    closed_at: datetime | None = None


class RemediationActionUpdate(BaseModel):
    ticket_ref: str | None = None
    status: str | None = None


class RemediationGroupPreview(BaseModel):
    plugin_name: str
    solution: str | None = None
    finding_count: int
    asset_count: int
    team_ids: list[int]
    max_caa_score: float | None = None
    finding_ids: list[int]
