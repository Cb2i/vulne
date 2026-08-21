"""
Rendements obligataires US (US10Y = DGS10, US02Y = DGS2) via l'API officielle
FRED (Federal Reserve Bank of St. Louis). Source niveau 1.

FRED ne publie qu'une observation par jour ouvrable (pas de tick intraday) :
c'est une caracteristique de la source, pas une limite du collecteur.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from ..config import get_secret

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"


@dataclass
class FredObservation:
    series_id: str
    date: str
    value: float | None
    fetched_at_utc: str


def get_latest_observation(series_id: str) -> FredObservation | None:
    api_key = get_secret("FRED_API_KEY")
    if not api_key:
        return None
    try:
        resp = httpx.get(
            FRED_BASE,
            params={
                "series_id": series_id,
                "api_key": api_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 1,
            },
            timeout=10,
        )
        resp.raise_for_status()
        payload = resp.json()
        obs = payload.get("observations", [])
        if not obs:
            return None
        latest = obs[0]
        value = None if latest["value"] == "." else float(latest["value"])
        return FredObservation(
            series_id=series_id,
            date=latest["date"],
            value=value,
            fetched_at_utc=datetime.now(timezone.utc).isoformat(),
        )
    except (httpx.HTTPError, ValueError, KeyError):
        return None


def get_us_yields() -> dict[str, FredObservation | None]:
    return {
        "US10Y": get_latest_observation("DGS10"),
        "US02Y": get_latest_observation("DGS2"),
    }
