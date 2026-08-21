"""
Collecteur OHLC / indicateurs marche via Twelve Data (source niveau 2 principale,
MCP officiel disponible sur mcp.twelvedata.com, API REST utilisee ici en fallback
direct pour un usage scripte/serveur).

Regle anti-hallucination : si la cle API est absente ou l'appel echoue (et le
fallback Alpha Vantage aussi), la fonction retourne None. Le rapport doit alors
afficher "Donnee non disponible / non verifiable", jamais une valeur inventee.
"""
from __future__ import annotations

from dataclasses import dataclass

import httpx

from ..config import get_secret

TWELVE_DATA_BASE = "https://api.twelvedata.com"
ALPHA_VANTAGE_BASE = "https://www.alphavantage.co/query"

TIMEFRAME_MAP = {"M15": "15min", "H1": "1h", "H4": "4h", "D1": "1day"}


@dataclass
class Candle:
    datetime: str
    open: float
    high: float
    low: float
    close: float


@dataclass
class MarketSnapshot:
    symbol: str
    timeframe: str
    candles: list[Candle]
    source: str
    fetched_at_utc: str


def _fetch_twelve_data(symbol: str, timeframe: str, outputsize: int) -> MarketSnapshot | None:
    api_key = get_secret("TWELVE_DATA_API_KEY")
    if not api_key:
        return None
    interval = TIMEFRAME_MAP.get(timeframe)
    if interval is None:
        raise ValueError(f"Timeframe non supporte: {timeframe}")
    try:
        resp = httpx.get(
            f"{TWELVE_DATA_BASE}/time_series",
            params={
                "symbol": symbol,
                "interval": interval,
                "outputsize": outputsize,
                "apikey": api_key,
            },
            timeout=10,
        )
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("status") == "error" or "values" not in payload:
            return None
    except (httpx.HTTPError, ValueError):
        return None

    from datetime import datetime, timezone

    candles = [
        Candle(
            datetime=v["datetime"],
            open=float(v["open"]),
            high=float(v["high"]),
            low=float(v["low"]),
            close=float(v["close"]),
        )
        for v in reversed(payload["values"])
    ]
    return MarketSnapshot(
        symbol=symbol,
        timeframe=timeframe,
        candles=candles,
        source="Twelve Data",
        fetched_at_utc=datetime.now(timezone.utc).isoformat(),
    )


def _fetch_alpha_vantage(symbol: str, timeframe: str) -> MarketSnapshot | None:
    api_key = get_secret("ALPHA_VANTAGE_API_KEY")
    if not api_key or timeframe != "D1":
        # Le plan gratuit Alpha Vantage (25 req/jour, EOD) ne convient qu'au fallback daily.
        return None
    from_symbol, to_symbol = "XAU", "USD"
    try:
        resp = httpx.get(
            ALPHA_VANTAGE_BASE,
            params={
                "function": "FX_DAILY",
                "from_symbol": from_symbol,
                "to_symbol": to_symbol,
                "apikey": api_key,
            },
            timeout=10,
        )
        resp.raise_for_status()
        payload = resp.json()
        series = payload.get("Time Series FX (Daily)")
        if not series:
            return None
    except (httpx.HTTPError, ValueError):
        return None

    from datetime import datetime, timezone

    items = sorted(series.items())[-30:]
    candles = [
        Candle(
            datetime=day,
            open=float(v["1. open"]),
            high=float(v["2. high"]),
            low=float(v["3. low"]),
            close=float(v["4. close"]),
        )
        for day, v in items
    ]
    return MarketSnapshot(
        symbol=f"{from_symbol}{to_symbol}",
        timeframe=timeframe,
        candles=candles,
        source="Alpha Vantage (fallback)",
        fetched_at_utc=datetime.now(timezone.utc).isoformat(),
    )


def get_market_snapshot(symbol: str = "XAU/USD", timeframe: str = "H1", outputsize: int = 200) -> MarketSnapshot | None:
    """Twelve Data d'abord, sinon Alpha Vantage (daily seulement), sinon None."""
    snapshot = _fetch_twelve_data(symbol, timeframe, outputsize)
    if snapshot is not None:
        return snapshot
    return _fetch_alpha_vantage(symbol, timeframe)
