"""
Indicateurs techniques calcules a partir de bougies OHLC reelles uniquement.
Aucune fonction ici n'invente de valeur : si la serie fournie est trop courte
pour un indicateur donne, la fonction retourne None pour cet indicateur.
"""
from __future__ import annotations

import pandas as pd

from ..collectors.market_data import Candle


def candles_to_df(candles: list[Candle]) -> pd.DataFrame:
    df = pd.DataFrame([c.__dict__ for c in candles])
    if df.empty:
        return df
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df.sort_values("datetime").reset_index(drop=True)


def ema(series: pd.Series, period: int) -> float | None:
    if len(series) < period:
        return None
    return float(series.ewm(span=period, adjust=False).mean().iloc[-1])


def rsi(series: pd.Series, period: int = 14) -> float | None:
    if len(series) < period + 1:
        return None
    delta = series.diff().dropna()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    last_gain, last_loss = float(avg_gain.iloc[-1]), float(avg_loss.iloc[-1])
    if last_loss == 0:
        return 100.0 if last_gain > 0 else 50.0
    rs = last_gain / last_loss
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> dict[str, float] | None:
    if len(series) < slow + signal:
        return None
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return {
        "macd": float(macd_line.iloc[-1]),
        "signal": float(signal_line.iloc[-1]),
        "histogram": float(histogram.iloc[-1]),
    }


def atr_series(df: pd.DataFrame, period: int = 14) -> pd.Series | None:
    """Serie complete de l'ATR (une valeur par bougie), pas seulement la derniere."""
    if len(df) < period + 1:
        return None
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    return tr.rolling(period).mean()


def atr(df: pd.DataFrame, period: int = 14) -> float | None:
    series = atr_series(df, period)
    if series is None:
        return None
    value = series.iloc[-1]
    return None if pd.isna(value) else float(value)


def atr_with_average(df: pd.DataFrame, period: int = 14, avg_lookback: int = 20) -> tuple[float | None, float | None]:
    """
    Retourne (ATR courant, moyenne des `avg_lookback` valeurs d'ATR precedentes),
    utilise par le Risk Engine pour comparer la volatilite actuelle a sa
    moyenne recente. (None, None) si l'historique fourni est insuffisant.
    """
    series = atr_series(df, period)
    if series is None:
        return None, None
    valid = series.dropna()
    if len(valid) < avg_lookback + 1:
        return None, None
    current = float(valid.iloc[-1])
    average = float(valid.iloc[-(avg_lookback + 1):-1].mean())
    return current, average


def range_amplitude_ratio(df: pd.DataFrame, recent: int = 3, lookback: int = 20) -> float | None:
    """
    Ratio entre l'amplitude (high - low) moyenne des `recent` dernieres
    bougies et celle des `lookback` bougies precedentes. Utilise pour
    detecter un sursaut de volatilite recent (ex. amplitude M15 apres une
    publication macro) sans jamais inventer de seuil : retourne None si
    l'historique est insuffisant.
    """
    if len(df) < recent + lookback:
        return None
    ranges = df["high"] - df["low"]
    recent_avg = ranges.tail(recent).mean()
    baseline = ranges.tail(recent + lookback).head(lookback).mean()
    if baseline == 0 or pd.isna(baseline) or pd.isna(recent_avg):
        return None
    return float(recent_avg / baseline)


def realized_volatility(df: pd.DataFrame, lookback: int = 20) -> float | None:
    """Ecart-type des rendements de cloture, en % annualise simplifie (info contextuelle)."""
    if len(df) < lookback + 1:
        return None
    returns = df["close"].pct_change().dropna().tail(lookback)
    if returns.empty:
        return None
    return float(returns.std() * 100)


def compute_all(candles: list[Candle]) -> dict:
    """Calcule tous les indicateurs demandes. Chaque cle peut etre None."""
    df = candles_to_df(candles)
    if df.empty:
        return {
            "ema20": None, "ema50": None, "ema200": None,
            "rsi14": None, "macd": None, "atr14": None,
            "volatility": None, "last_close": None,
        }
    close = df["close"]
    return {
        "ema20": ema(close, 20),
        "ema50": ema(close, 50),
        "ema200": ema(close, 200),
        "rsi14": rsi(close, 14),
        "macd": macd(close),
        "atr14": atr(df, 14),
        "volatility": realized_volatility(df),
        "last_close": float(close.iloc[-1]),
    }
