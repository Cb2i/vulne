"""
Conversion de fuseaux horaires DST-safe (America/Montreal <-> UTC/autres).

Regle absolue : ne jamais coder un decalage fixe (ex. "UTC-5" en dur). Les
regles de changement d'heure de l'IANA tzdata gerent automatiquement les
transitions EST/EDT (Canada/US), GMT/BST (UK) et CET/CEST (zone euro), qui ne
sont pas synchronisees entre elles (ex. l'UE change une a deux semaines avant
les US certaines annees).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo

MONTREAL = ZoneInfo("America/Montreal")
NEW_YORK = ZoneInfo("America/New_York")
LONDON = ZoneInfo("Europe/London")
TOKYO = ZoneInfo("Asia/Tokyo")
UTC = ZoneInfo("UTC")


def to_montreal(dt: datetime) -> datetime:
    """Convertit un datetime timezone-aware vers America/Montreal."""
    if dt.tzinfo is None:
        raise ValueError("datetime doit etre timezone-aware")
    return dt.astimezone(MONTREAL)


def now_montreal() -> datetime:
    return datetime.now(MONTREAL)


@dataclass(frozen=True)
class SessionWindow:
    name: str
    start_montreal: datetime
    end_montreal: datetime


def session_window_for_day(
    zone: ZoneInfo, open_time: time, close_time: time, reference_date_montreal: datetime, name: str
) -> SessionWindow:
    """
    Calcule la fenetre d'une session (ex. Londres 08:00-16:30 heure locale de
    session) et la convertit en America/Montreal pour la date de reference
    donnee. Recalcule chaque appel : ne suppose jamais un decalage constant.
    """
    local_date = reference_date_montreal.astimezone(zone).date()
    start_local = datetime.combine(local_date, open_time, tzinfo=zone)
    end_local = datetime.combine(local_date, close_time, tzinfo=zone)
    if end_local <= start_local:
        # session traversant minuit heure locale
        from datetime import timedelta

        end_local += timedelta(days=1)
    return SessionWindow(
        name=name,
        start_montreal=start_local.astimezone(MONTREAL),
        end_montreal=end_local.astimezone(MONTREAL),
    )


def overlap(a: SessionWindow, b: SessionWindow) -> tuple[datetime, datetime] | None:
    start = max(a.start_montreal, b.start_montreal)
    end = min(a.end_montreal, b.end_montreal)
    if start >= end:
        return None
    return start, end


def fmt_hm(dt: datetime) -> str:
    return dt.strftime("%H:%M")
