from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ExceptionStatus
from app.models.mixins import TimestampMixin


class ExceptionRecord(Base, TimestampMixin):
    """A risk-acceptance exception, matching the 'Exceptions' sheet."""

    __tablename__ = "exceptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    vulnerability_match: Mapped[str] = mapped_column(String(500))  # plugin name / CVE pattern
    asset_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hostname_pattern: Mapped[str | None] = mapped_column(String(255), nullable=True)
    granted_by: Mapped[str] = mapped_column(String(255))
    granted_at: Mapped[date] = mapped_column(Date)
    expires_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    confluence_link: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ExceptionStatus] = mapped_column(default=ExceptionStatus.ACTIVE)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    findings: Mapped[list["Finding"]] = relationship(back_populates="exception")
