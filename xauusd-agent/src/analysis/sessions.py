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


def session_flags(reference_dt_montreal: datetime) -> dict:
    """
    Indique si `reference_dt_montreal` tombe dans le chevauchement Londres/New
    York ou dans une seule des deux sessions, pour alimenter le facteur
    "Session/chevauchement" du Risk Engine (jusqu'ici toujours code en dur a
    False, ce qui desactivait ce facteur en permanence).
    """
    london = session_window_for_day(LONDON, time(8, 0), time(16, 30), reference_dt_montreal, "Londres")
    new_york = session_window_for_day(NEW_YORK, time(8, 0), time(17, 0), reference_dt_montreal, "New York")
    overlap_window = overlap(london, new_york)

    in_overlap = overlap_window is not None and overlap_window[0] <= reference_dt_montreal <= overlap_window[1]
    in_london = london.start_montreal <= reference_dt_montreal <= london.end_montreal
    in_new_york = new_york.start_montreal <= reference_dt_montreal <= new_york.end_montreal
    in_single_session = (in_london or in_new_york) and not in_overlap

    return {"in_overlap": in_overlap, "in_single_session": in_single_session}
