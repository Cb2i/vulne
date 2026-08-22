"""
Calendrier economique : Trading Economics (MCP officiel mcp.tradingeconomics.com,
API REST ici) en priorite si une cle est configuree, sinon fallback ForexFactory
(non officiel). Dans tous les cas, tout evenement utilise pour le Risk Score doit
etre recoupe avec la source officielle (Fed/BLS/BEA) avant d'etre marque "confirme"
- ce recoupement se fait dans le Risk Engine, pas ici.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from ..config import get_secret

TE_BASE = "https://api.tradingeconomics.com/calendar"

HIGH_IMPACT_KEYWORDS = (
    "CPI", "Core CPI", "PPI", "PCE", "Core PCE", "Nonfarm Payrolls", "NFP",
    "Unemployment Rate", "Jobless Claims", "ADP", "GDP", "Retail Sales",
    "ISM Manufacturing", "ISM Services", "PMI", "JOLTS", "Consumer Confidence",
    "Michigan", "Durable Goods", "FOMC", "Fed Interest Rate", "Powell",
)


@dataclass
class CalendarEvent:
    datetime_utc: str
    country: str
    event: str
    importance: str  # low / medium / high
    consensus: str | None
    previous: str | None
    actual: str | None
    source: str


@dataclass
class CalendarResult:
    events: list[CalendarEvent]
    verified: bool  # True si une source a reellement repondu (meme avec 0 evenement)
    source: str | None  # nom de la source qui a repondu, None si aucune n'a repondu


def _fetch_trading_economics(country: str, start: str, end: str) -> list[CalendarEvent] | None:
    api_key = get_secret("TRADING_ECONOMICS_API_KEY")
    if not api_key:
        return None
    try:
        resp = httpx.get(
            f"{TE_BASE}/country/{country}",
            params={"c": api_key, "d1": start, "d2": end},
            timeout=10,
        )
        resp.raise_for_status()
        payload = resp.json()
    except (httpx.HTTPError, ValueError):
        return None

    events = []
    for item in payload:
        events.append(
            CalendarEvent(
                datetime_utc=item.get("Date", ""),
                country=item.get("Country", country),
                event=item.get("Event", ""),
                importance={1: "low", 2: "medium", 3: "high"}.get(item.get("Importance"), "medium"),
                consensus=str(item.get("Forecast")) if item.get("Forecast") is not None else None,
                previous=str(item.get("Previous")) if item.get("Previous") is not None else None,
                actual=str(item.get("Actual")) if item.get("Actual") is not None else None,
                source="Trading Economics",
            )
        )
    return events


def get_calendar(country: str = "united states", start: str | None = None, end: str | None = None) -> CalendarResult:
    """
    Retourne les evenements connus ET si une source a reellement repondu.

    Important : une liste vide ne veut pas forcement dire "verifie, rien de
    prevu aujourd'hui" - ca peut aussi vouloir dire "aucune source de
    calendrier configuree, on n'a jamais verifie". Confondre les deux ferait
    lire un Risk Score base sur "aucun evenement" comme une garantie alors
    qu'il peut simplement n'avoir jamais ete verifie. `verified` distingue
    explicitement les deux cas pour que le rapport ne les confonde pas.
    """
    now = datetime.now(timezone.utc)
    start = start or now.strftime("%Y-%m-%d")
    end = end or now.strftime("%Y-%m-%d")
    events = _fetch_trading_economics(country, start, end)
    if events is not None:
        return CalendarResult(events=events, verified=True, source="Trading Economics")
    # Fallback ForexFactory non branche par defaut (scraping non officiel) :
    # a activer explicitement dans une extension du projet si l'utilisateur
    # accepte les conditions d'utilisation de ForexFactory.
    return CalendarResult(events=[], verified=False, source=None)


def is_high_impact(event_name: str) -> bool:
    return any(keyword.lower() in event_name.lower() for keyword in HIGH_IMPACT_KEYWORDS)
