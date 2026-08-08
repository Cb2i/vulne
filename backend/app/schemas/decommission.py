from datetime import date

from pydantic import BaseModel, ConfigDict


class DecommissionCreate(BaseModel):
    hostname: str
    decommissioned_at: date | None = None
    reason: str | None = None


class DecommissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    hostname: str
    decommissioned_at: date | None = None
    reason: str | None = None
    asset_id: int | None = None
