"""Configurable rule engines: CAA weighting, SLE delays, ownership (team) assignment."""
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import Severity
from app.models.mixins import TimestampMixin


class CAAConfig(Base, TimestampMixin):
    """Contextual Asset Adjustment (CAA) score weighting. A single active config is used at a
    time; keeping history allows past findings to show which config produced their score."""

    __tablename__ = "caa_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), default="Default CAA config")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Exposition weights (added to raw CVSS, in points)
    weight_exposition_internet: Mapped[float] = mapped_column(Float, default=1.5)
    weight_exposition_dmz: Mapped[float] = mapped_column(Float, default=0.5)
    weight_exposition_internal: Mapped[float] = mapped_column(Float, default=-0.5)
    weight_exposition_airgapped: Mapped[float] = mapped_column(Float, default=-2.0)

    # Asset criticality weights
    weight_criticite_critical: Mapped[float] = mapped_column(Float, default=2.5)
    weight_criticite_high: Mapped[float] = mapped_column(Float, default=1.5)
    weight_criticite_medium: Mapped[float] = mapped_column(Float, default=0.0)
    weight_criticite_low: Mapped[float] = mapped_column(Float, default=-1.0)

    # Exploitability
    weight_exploitable: Mapped[float] = mapped_column(Float, default=2.0)

    # Overall multiplier applied after the raw sum, scaled back to a 0-10 range.
    normalization_divisor: Mapped[float] = mapped_column(Float, default=1.0)

    sle_rules: Mapped[list["SLERule"]] = relationship(back_populates="caa_config")


class SLERule(Base, TimestampMixin):
    """Service Level Expectation: remediation delay (in days) per CAA severity bucket."""

    __tablename__ = "sle_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    caa_config_id: Mapped[int | None] = mapped_column(ForeignKey("caa_configs.id"), nullable=True)
    severity: Mapped[Severity] = mapped_column(unique=True)
    caa_min: Mapped[float] = mapped_column(Float)
    caa_max: Mapped[float] = mapped_column(Float)
    delay_days: Mapped[int] = mapped_column(Integer)

    caa_config: Mapped["CAAConfig"] = relationship(back_populates="sle_rules")


class OwnershipRule(Base, TimestampMixin):
    """Team assignment rule, matching the 'KPI' sheet (Equipes / Champ_nom d'hôtes / Champ_OS).

    hostname_pattern / os_pattern are simple case-insensitive substring or 'commence par X'
    (starts-with) expressions evaluated by the ownership engine. Rules are evaluated in
    ascending `priority` order; the first match wins.
    """

    __tablename__ = "ownership_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    hostname_pattern: Mapped[str | None] = mapped_column(String(255), nullable=True)
    os_pattern: Mapped[str | None] = mapped_column(String(255), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    team: Mapped["Team"] = relationship(back_populates="ownership_rules")
