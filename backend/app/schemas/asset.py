from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AssetBase(BaseModel):
    hostname: str
    fqdn: str | None = None
    ip_address: str | None = None
    os: str | None = None
    exposition: str = "Internal"
    criticite: str = "Medium"
    classification: str | None = None


class AssetUpdate(BaseModel):
    exposition: str | None = None
    criticite: str | None = None
    classification: str | None = None
    team_id: int | None = None


class AssetRead(AssetBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    team_id: int | None = None
    grade_actif: str | None = None
    score_actif: float | None = None
    last_seen_at: datetime | None = None
    is_decommissioned: bool
