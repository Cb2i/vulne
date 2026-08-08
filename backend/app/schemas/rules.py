from pydantic import BaseModel, ConfigDict

from app.models.enums import Severity


class CAAConfigBase(BaseModel):
    name: str
    description: str | None = None
    weight_exposition_internet: float
    weight_exposition_dmz: float
    weight_exposition_internal: float
    weight_exposition_airgapped: float
    weight_criticite_critical: float
    weight_criticite_high: float
    weight_criticite_medium: float
    weight_criticite_low: float
    weight_exploitable: float
    normalization_divisor: float = 1.0


class CAAConfigCreate(CAAConfigBase):
    pass


class CAAConfigUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    weight_exposition_internet: float | None = None
    weight_exposition_dmz: float | None = None
    weight_exposition_internal: float | None = None
    weight_exposition_airgapped: float | None = None
    weight_criticite_critical: float | None = None
    weight_criticite_high: float | None = None
    weight_criticite_medium: float | None = None
    weight_criticite_low: float | None = None
    weight_exploitable: float | None = None
    normalization_divisor: float | None = None
    is_active: bool | None = None


class CAAConfigRead(CAAConfigBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool


class SLERuleBase(BaseModel):
    severity: Severity
    caa_min: float
    caa_max: float
    delay_days: int


class SLERuleUpdate(BaseModel):
    caa_min: float | None = None
    caa_max: float | None = None
    delay_days: int | None = None


class SLERuleRead(SLERuleBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class OwnershipRuleBase(BaseModel):
    team_id: int
    hostname_pattern: str | None = None
    os_pattern: str | None = None
    priority: int = 100
    active: bool = True


class OwnershipRuleCreate(OwnershipRuleBase):
    pass


class OwnershipRuleUpdate(BaseModel):
    team_id: int | None = None
    hostname_pattern: str | None = None
    os_pattern: str | None = None
    priority: int | None = None
    active: bool | None = None


class OwnershipRuleRead(OwnershipRuleBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
