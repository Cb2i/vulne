from datetime import datetime, timedelta

from src.risk.risk_engine import compute_risk_score, is_volatility_normalized
from src.timezones import MONTREAL


def test_score_capped_at_10():
    now = datetime(2026, 1, 15, 8, 0, tzinfo=MONTREAL)
    risk = compute_risk_score(
        next_major_event_dt=now + timedelta(minutes=5),
        now=now,
        is_major_event=True,
        atr14=3.0,
        atr_avg20=1.0,
        m15_amplitude_ratio=3.0,
        in_session_overlap=True,
        in_single_session=True,
        dxy_change_pct=1.0,
        us10y_change_bp=20,
        confirmed_major_news=True,
    )
    assert risk.total_score == 10.0
    assert risk.level == "exceptionnel"
    assert risk.emoji == "🚨"


def test_score_low_when_nothing_happening():
    now = datetime(2026, 1, 15, 3, 0, tzinfo=MONTREAL)
    risk = compute_risk_score(next_major_event_dt=None, now=now, is_major_event=False)
    assert risk.total_score == 0.0
    assert risk.level == "faible"
    assert risk.emoji == "🟢"


def test_event_far_away_scores_lower_than_event_imminent():
    now = datetime(2026, 1, 15, 3, 0, tzinfo=MONTREAL)
    near = compute_risk_score(next_major_event_dt=now + timedelta(minutes=10), now=now, is_major_event=True)
    far = compute_risk_score(next_major_event_dt=now + timedelta(hours=20), now=now, is_major_event=True)
    assert near.total_score > far.total_score


def test_normalization_requires_both_atr_and_m15_confirmation():
    assert is_volatility_normalized(atr14=1.0, atr_avg20=1.0, m15_amplitude_ratio=1.0) is True
    assert is_volatility_normalized(atr14=2.0, atr_avg20=1.0, m15_amplitude_ratio=1.0) is False
    assert is_volatility_normalized(atr14=None, atr_avg20=1.0, m15_amplitude_ratio=1.0) is False
