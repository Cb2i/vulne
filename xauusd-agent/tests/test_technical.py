from src.analysis.technical import atr, compute_all, ema, rsi
from src.collectors.market_data import Candle


def make_candles(closes: list[float]) -> list[Candle]:
    return [
        Candle(datetime=f"2026-01-{i+1:02d}", open=c, high=c + 1, low=c - 1, close=c)
        for i, c in enumerate(closes)
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
