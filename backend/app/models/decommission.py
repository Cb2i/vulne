from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Decommission(Base, TimestampMixin):
    """Record of a decommissioned asset, matching the 'Décommissionés' sheet."""

    __tablename__ = "decommissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id"), nullable=True)
    hostname: Mapped[str] = mapped_column(String(255), index=True)
    decommissioned_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decommissioned_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    asset: Mapped["Asset"] = relationship()
