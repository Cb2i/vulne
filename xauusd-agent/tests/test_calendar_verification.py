"""
"Sources sures et exactes" : une liste d'evenements vide ne doit jamais se
lire comme "verifie, rien de prevu" quand en realite aucune source de
calendrier n'a repondu. Ces tests figent ce comportement.
"""
from datetime import datetime, timedelta

from src.collectors.economic_calendar import CalendarEvent, CalendarResult
from src.risk.risk_engine import compute_risk_score
from src.risk.timeline import build_risk_timeline
from src.timezones import MONTREAL


def test_calendar_result_distinguishes_unverified_from_verified_empty():
    unverified = CalendarResult(events=[], verified=False, source=None)
    verified_empty = CalendarResult(events=[], verified=True, source="Trading Economics")
    assert unverified.events == verified_empty.events == []
    assert unverified.verified is False
    assert verified_empty.verified is True


def test_timeline_flags_unverified_calendar_distinctly():
    day_start = datetime(2026, 1, 15, 0, 0, tzinfo=MONTREAL)
    day_end = datetime(2026, 1, 15, 23, 59, tzinfo=MONTREAL)

    unverified_timeline = build_risk_timeline([], day_start, day_end, calendar_verified=False)
    verified_timeline = build_risk_timeline([], day_start, day_end, calendar_verified=True)

    assert unverified_timeline[0].level == "🟠"
    assert "non verifie" in unverified_timeline[0].reason.lower()
    assert verified_timeline[0].level == "🟢"
    assert "verifie" in verified_timeline[0].reason.lower()
    assert "non verifie" not in verified_timeline[0].reason.lower()


def test_risk_score_reason_flags_unverified_calendar():
    now = datetime(2026, 1, 15, 8, 0, tzinfo=MONTREAL)
    unverified = compute_risk_score(next_major_event_dt=None, now=now, is_major_event=False, calendar_verified=False)
    verified = compute_risk_score(next_major_event_dt=None, now=now, is_major_event=False, calendar_verified=True)

    proximity_unverified = next(f for f in unverified.factors if f.name == "Proximite evenement macro")
    proximity_verified = next(f for f in verified.factors if f.name == "Proximite evenement macro")

    assert "non verifie" in proximity_unverified.reason.lower()
    assert "verifie" in proximity_verified.reason.lower()
    assert "non verifie" not in proximity_verified.reason.lower()
    # Le score chiffre reste le meme (0) : on ne fabrique pas de points a partir
    # d'une absence d'information, on se contente de rendre l'incertitude visible.
    assert unverified.total_score == verified.total_score == 0.0
