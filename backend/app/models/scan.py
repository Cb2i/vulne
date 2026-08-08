from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ImportStatus
from app.models.mixins import TimestampMixin


class Scan(Base, TimestampMixin):
    """One Tenable export ('Nom du scan'), imported as a batch of findings."""

    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    source_filename: Mapped[str | None] = mapped_column(String(500), nullable=True)
    imported_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finding_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[ImportStatus] = mapped_column(default=ImportStatus.SUCCESS)
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    findings: Mapped[list["Finding"]] = relationship(back_populates="scan")
    imported_by: Mapped["User"] = relationship()
