from datetime import date, timedelta

from app.models.enums import Severity
from app.models.rules import SLERule
from app.rules.sle.engine import resolve_sle

RULES = [
    SLERule(severity=Severity.CRITIQUE, caa_min=8.5, caa_max=10.0, delay_days=15),
    SLERule(severity=Severity.HAUTE, caa_min=6.5, caa_max=8.49, delay_days=30),
    SLERule(severity=Severity.MOYENNE, caa_min=4.0, caa_max=6.49, delay_days=90),
    SLERule(severity=Severity.FAIBLE, caa_min=0.0, caa_max=3.99, delay_days=180),
]


def test_resolve_sle_matches_correct_bucket():
    result = resolve_sle(9.0, RULES, from_date=date(2026, 1, 1))
    assert result.severity == Severity.CRITIQUE
    assert result.delay_days == 15
    assert result.due_date == date(2026, 1, 1) + timedelta(days=15)


def test_resolve_sle_boundary_values():
    assert resolve_sle(8.49, RULES).severity == Severity.HAUTE
    assert resolve_sle(8.5, RULES).severity == Severity.CRITIQUE
    assert resolve_sle(0.0, RULES).severity == Severity.FAIBLE


def test_resolve_sle_falls_back_when_no_rules():
    result = resolve_sle(5.0, [])
    assert result.delay_days == 180
