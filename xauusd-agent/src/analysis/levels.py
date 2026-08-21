"""Niveaux cles : PDH/PDL, plus haut/bas hebdo, zones psychologiques."""
from __future__ import annotations

import pandas as pd

from ..collectors.market_data import Candle
from .technical import candles_to_df


def previous_day_high_low(daily_candles: list[Candle]) -> dict[str, float | None]:
    df = candles_to_df(daily_candles)
    if len(df) < 2:
        return {"previous_day_high": None, "previous_day_low": None}
    prev = df.iloc[-2]
    return {"previous_day_high": float(prev["high"]), "previous_day_low": float(prev["low"])}


def weekly_high_low(daily_candles: list[Candle], days: int = 5) -> dict[str, float | None]:
    df = candles_to_df(daily_candles)
    if df.empty:
        return {"weekly_high": None, "weekly_low": None}
    window = df.tail(days)
    return {"weekly_high": float(window["high"].max()), "weekly_low": float(window["low"].min())}


def psychological_levels(last_close: float | None, step: float = 50.0, span: int = 2) -> list[float]:
    """Zones rondes (ex. paliers de 50) autour du prix courant. step/span configurables."""
    if last_close is None:
        return []
    base = round(last_close / step) * step
    return [base + i * step for i in range(-span, span + 1)]


def support_resistance_from_swings(h1_candles: list[Candle], lookback: int = 60) -> dict[str, list[float]]:
    """
    Supports/resistances approximes par les plus hauts/bas locaux (swing highs/lows)
    sur les `lookback` dernieres bougies H1. Methode simple, deterministe, basee
    uniquement sur les donnees fournies (pas d'estimation subjective).
    """
    df = candles_to_df(h1_candles).tail(lookback)
    if len(df) < 5:
        return {"resistances": [], "supports": []}
    highs, lows = [], []
    for i in range(2, len(df) - 2):
        window_h = df["high"].iloc[i - 2 : i + 3]
        window_l = df["low"].iloc[i - 2 : i + 3]
        if df["high"].iloc[i] == window_h.max():
            highs.append(float(df["high"].iloc[i]))
        if df["low"].iloc[i] == window_l.min():
            lows.append(float(df["low"].iloc[i]))
    resistances = sorted(set(round(h, 2) for h in highs), reverse=True)[:3]
    supports = sorted(set(round(l, 2) for l in lows), reverse=True)[:3]
    return {"resistances": resistances, "supports": supports}
