from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ScanObservation(Base):
    """Append-only record that a given Finding was present in a given Scan's import.

    Findings are deduplicated across imports (the same vulnerability instance is one
    Finding row that persists across scans until remediated), so Finding.scan_id alone
    cannot answer "was this finding part of scan X's results" once it has been re-observed
    in a later scan. This table keeps that per-scan membership immutable, which is what
    scan comparison and same-series remediation detection rely on.
    """

    __tablename__ = "scan_observations"

    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id"), index=True)
    finding_id: Mapped[int] = mapped_column(ForeignKey("findings.id"), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    scan: Mapped["Scan"] = relationship()
    finding: Mapped["Finding"] = relationship()
