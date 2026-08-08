from datetime import date

from pydantic import BaseModel, ConfigDict

from app.models.enums import ExceptionStatus


class ExceptionBase(BaseModel):
    vulnerability_match: str
    asset_type: str | None = None
    hostname_pattern: str | None = None
    granted_by: str
    granted_at: date
    expires_at: date | None = None
    confluence_link: str | None = None
    justification: str | None = None


class ExceptionCreate(ExceptionBase):
    pass


class ExceptionUpdate(BaseModel):
    vulnerability_match: str | None = None
    asset_type: str | None = None
    hostname_pattern: str | None = None
    expires_at: date | None = None
    confluence_link: str | None = None
    justification: str | None = None
    status: ExceptionStatus | None = None


class ExceptionRead(ExceptionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: ExceptionStatus
