"""Sessions internationales converties en America/Montreal, recalculees chaque jour (DST-safe)."""
from __future__ import annotations

from datetime import datetime, time

from ..timezones import LONDON, MONTREAL, NEW_YORK, TOKYO, SessionWindow, fmt_hm, overlap, session_window_for_day


def build_sessions(reference_dt_montreal: datetime) -> dict:
    asia = session_window_for_day(TOKYO, time(9, 0), time(18, 0), reference_dt_montreal, "Asie (Tokyo)")
    london = session_window_for_day(LONDON, time(8, 0), time(16, 30), reference_dt_montreal, "Londres")
    new_york = session_window_for_day(NEW_YORK, time(8, 0), time(17, 0), reference_dt_montreal, "New York")

    overlap_window = overlap(london, new_york)

    def fmt(session: SessionWindow) -> str:
        return f"{fmt_hm(session.start_montreal)} - {fmt_hm(session.end_montreal)}"

    return {
        "asia": fmt(asia),
        "london": fmt(london),
        "new_york": fmt(new_york),
        "overlap_london_ny": (
            f"{fmt_hm(overlap_window[0])} - {fmt_hm(overlap_window[1])}" if overlap_window else "aucun"
        ),
    }
