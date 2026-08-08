from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class RemediationAction(Base, TimestampMixin):
    """A consolidated remediation action grouping several findings that share the same
    plugin/solution (regroupement des remédiations), so a team can fix them in one pass."""

    __tablename__ = "remediation_actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    plugin_name: Mapped[str] = mapped_column(String(500), index=True)
    solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    ticket_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open")
    finding_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    team: Mapped["Team"] = relationship()
    items: Mapped[list["RemediationActionFinding"]] = relationship(back_populates="action")


class RemediationActionFinding(Base):
    """Join table linking a RemediationAction to the Findings it groups."""

    __tablename__ = "remediation_action_findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    action_id: Mapped[int] = mapped_column(ForeignKey("remediation_actions.id"), index=True)
    finding_id: Mapped[int] = mapped_column(ForeignKey("findings.id"), index=True)

    action: Mapped["RemediationAction"] = relationship(back_populates="items")
    finding: Mapped["Finding"] = relationship()
