from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Asset(Base, TimestampMixin):
    """A scanned host/asset, deduplicated by hostname across scans."""

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    hostname: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    fqdn: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    os: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Context used by the CAA engine, sourced from the "Analyse des tags des actifs" sheet.
    exposition: Mapped[str] = mapped_column(String(50), default="Internal")
    criticite: Mapped[str] = mapped_column(String(50), default="Medium")
    classification: Mapped[str | None] = mapped_column(String(100), nullable=True)

    grade_actif: Mapped[str | None] = mapped_column(String(5), nullable=True)
    score_actif: Mapped[float | None] = mapped_column(nullable=True)

    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)

    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_decommissioned: Mapped[bool] = mapped_column(Boolean, default=False)

    team: Mapped["Team"] = relationship(back_populates="assets")
    findings: Mapped[list["Finding"]] = relationship(back_populates="asset")
