from datetime import datetime, timedelta

from src.analysis.levels import support_resistance_from_swings
from src.collectors.market_data import Candle


def make_swing_candles() -> list[Candle]:
    """
    Construit une serie H1 avec des swing highs/lows connus, certains au-dessus
    et d'autres en dessous d'un prix de reference (110), pour verifier que le
    filtrage par last_close place bien chaque niveau du bon cote.
    """
    start = datetime(2026, 1, 1)
    # Motif repete en zigzag pour generer des swing highs/lows detectables
    # (fenetre de detection = 2 bougies avant/apres).
    pattern_highs_lows = [
        (105, 95), (108, 98), (112, 102), (95, 85), (98, 88),
        (120, 110), (118, 108), (90, 80), (92, 82), (115, 105),
    ]
    candles = []
    for i, (h, l) in enumerate(pattern_highs_lows):
        candles.append(
            Candle(datetime=(start + timedelta(hours=i)).isoformat(), open=(h + l) / 2, high=h, low=l, close=(h + l) / 2)
        )
    return candles


def test_resistances_stay_above_and_supports_below_last_close():
    candles = make_swing_candles()
    last_close = 110.0
    result = support_resistance_from_swings(candles, lookback=60, last_close=last_close)
    for r in result["resistances"]:
        assert r >= last_close, f"resistance {r} devrait etre >= {last_close}"
    for s in result["supports"]:
        assert s <= last_close, f"support {s} devrait etre <= {last_close}"


def test_no_filter_when_last_close_not_provided():
    candles = make_swing_candles()
    result = support_resistance_from_swings(candles, lookback=60)
    assert isinstance(result["resistances"], list)
    assert isinstance(result["supports"], list)
