from datetime import datetime, timedelta

from src.analysis.technical import atr, atr_with_average, candles_to_df, compute_all, ema, range_amplitude_ratio, rsi
from src.collectors.market_data import Candle


def make_candles(closes: list[float]) -> list[Candle]:
    return [
        Candle(datetime=f"2026-01-{i+1:02d}", open=c, high=c + 1, low=c - 1, close=c)
        for i, c in enumerate(closes)
    ]


def make_candles_with_range(ranges: list[float], base: float = 100.0) -> list[Candle]:
    """Bougies datees heure par heure (pas de limite a 28-31 items), amplitude controlee par `ranges`."""
    start = datetime(2026, 1, 1)
    return [
        Candle(
            datetime=(start + timedelta(hours=i)).isoformat(),
            open=base,
            high=base + r / 2,
            low=base - r / 2,
            close=base,
        )
        for i, r in enumerate(ranges)
    ]


def test_ema_none_when_insufficient_data():
    import pandas as pd

    series = pd.Series([1.0, 2.0, 3.0])
    assert ema(series, 20) is None


def test_ema_matches_known_value():
    import pandas as pd

    series = pd.Series([float(i) for i in range(1, 31)])
    value = ema(series, 5)
    expected = series.ewm(span=5, adjust=False).mean().iloc[-1]
    assert value == expected


def test_rsi_all_gains_is_100():
    import pandas as pd

    series = pd.Series([float(i) for i in range(1, 30)])  # strictement croissant
    value = rsi(series, 14)
    assert value is not None
    assert value > 95


def test_compute_all_returns_none_fields_on_empty_data():
    result = compute_all([])
    assert result["ema20"] is None
    assert result["rsi14"] is None
    assert result["last_close"] is None


def test_atr_none_when_insufficient_data():
    candles = make_candles([100.0, 101.0, 102.0])
    import pandas as pd

    df = pd.DataFrame([c.__dict__ for c in candles])
    assert atr(df, 14) is None


def test_atr_with_average_none_when_insufficient_history():
    candles = make_candles_with_range([2.0] * 20)  # < period(14) + avg_lookback(20) + 1
    df = candles_to_df(candles)
    current, average = atr_with_average(df, period=14, avg_lookback=20)
    assert current is None
    assert average is None


def test_atr_with_average_detects_recent_spike():
    # 40 bougies calmes (amplitude 2) puis un pic recent (amplitude 20) : l'ATR
    # courant doit ressortir nettement au-dessus de la moyenne des 20 precedents.
    ranges = [2.0] * 40 + [20.0] * 3
    candles = make_candles_with_range(ranges)
    df = candles_to_df(candles)
    current, average = atr_with_average(df, period=3, avg_lookback=20)
    assert current is not None and average is not None
    assert current > average * 1.5


def test_range_amplitude_ratio_detects_recent_spike():
    ranges = [1.0] * 20 + [5.0] * 3
    candles = make_candles_with_range(ranges)
    df = candles_to_df(candles)
    ratio = range_amplitude_ratio(df, recent=3, lookback=20)
    assert ratio is not None
    assert ratio > 2.0


def test_range_amplitude_ratio_none_when_insufficient_data():
    candles = make_candles_with_range([1.0] * 5)
    df = candles_to_df(candles)
    assert range_amplitude_ratio(df, recent=3, lookback=20) is None
