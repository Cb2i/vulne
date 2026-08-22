"""Construction de la timeline horaire du risque a partir du calendrier reel du jour."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from ..collectors.economic_calendar import CalendarEvent, is_high_impact


@dataclass
class RiskTimelineEntry:
    start_montreal: str
    end_montreal: str
    level: str  # emoji
    reason: str


def build_risk_timeline(
    events_montreal: list[tuple[datetime, CalendarEvent]],
    day_start: datetime,
    day_end: datetime,
    pre_event_minutes: int = 15,
    post_event_minutes: int = 45,
    calendar_verified: bool = True,
) -> list[RiskTimelineEntry]:
    """
    events_montreal: liste de (heure_montreal, evenement). day_start/day_end
    delimitent la journee a couvrir. Retourne une timeline triee et fusionnee.
    Aucune heure n'est inventee : uniquement celles fournies par les evenements
    reels (calendrier officiel/Trading Economics/ForexFactory).

    `calendar_verified` distingue "calendrier verifie, rien de majeur" (🟢,
    affirmatif) de "aucune source de calendrier n'a repondu" (🟠, on ne sait
    juste pas) : une liste d'evenements vide ne veut pas dire la meme chose
    dans ces deux cas, et le rapport ne doit jamais laisser le second se
    lire comme le premier.
    """
    segments: list[tuple[datetime, datetime, str, str]] = []
    major = [(dt, ev) for dt, ev in events_montreal if is_high_impact(ev.event)]

    if not major and not calendar_verified:
        segments.append(
            (
                day_start,
                day_end,
                "🟠",
                "Calendrier economique non verifie (source indisponible) : presence d'un evenement majeur non confirmee",
            )
        )
    elif not major:
        segments.append((day_start, day_end, "🟢", "Calendrier verifie : aucune publication macro majeure identifiee"))
    else:
        cursor = day_start
        for dt, ev in sorted(major, key=lambda x: x[0]):
            pre_start = dt - timedelta(minutes=pre_event_minutes)
            post_end = dt + timedelta(minutes=post_event_minutes)
            if pre_start > cursor:
                segments.append((cursor, pre_start, "🟢", "Conditions normales"))
            segments.append((pre_start, dt, "🟠", f"Approche de la publication : {ev.event}"))
            segments.append((dt, post_end, "🔴", f"Publication : {ev.event}"))
            cursor = post_end
        if cursor < day_end:
            segments.append(
                (
                    cursor,
                    day_end,
                    "🟠",
                    "Surveillance post-publication : attendre confirmation de normalisation de la volatilite",
                )
            )

    return [
        RiskTimelineEntry(
            start_montreal=s.strftime("%H:%M"),
            end_montreal=e.strftime("%H:%M"),
            level=level,
            reason=reason,
        )
        for s, e, level, reason in segments
    ]
