from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import FindingStatus, Severity
from app.models.mixins import TimestampMixin


class Finding(Base, TimestampMixin):
    """A single vulnerability instance (plugin x asset) coming from a Tenable scan row."""

    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id"), index=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)

    # Raw Tenable fields
    plugin_name: Mapped[str] = mapped_column(String(500), index=True)
    cve: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    grade: Mapped[str | None] = mapped_column(String(5), nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    protocol: Mapped[str | None] = mapped_column(String(20), nullable=True)
    port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    cvss_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cvss: Mapped[float | None] = mapped_column(Float, nullable=True)
    exploitable: Mapped[bool] = mapped_column(Boolean, default=False)

    # Computed by the business-logic engines
    caa_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    caa_severity: Mapped[Severity | None] = mapped_column(nullable=True)
    sle_delay_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sle_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)

    status: Mapped[FindingStatus] = mapped_column(default=FindingStatus.OPEN, index=True)
    remediation_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    ticket_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    exception_id: Mapped[int | None] = mapped_column(ForeignKey("exceptions.id"), nullable=True)

    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    scan: Mapped["Scan"] = relationship(back_populates="findings")
    asset: Mapped["Asset"] = relationship(back_populates="findings")
    team: Mapped["Team"] = relationship()
    exception: Mapped["ExceptionRecord"] = relationship(back_populates="findings")
