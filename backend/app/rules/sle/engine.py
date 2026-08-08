"""SLE (Service Level Expectation) engine: maps a CAA score to a severity bucket
and a remediation delay (in days), using the configurable SLERule table."""
from dataclasses import dataclass
from datetime import date, timedelta

from app.models.enums import Severity
from app.models.rules import SLERule

DEFAULT_SEVERITY_ORDER = [Severity.CRITIQUE, Severity.HAUTE, Severity.MOYENNE, Severity.FAIBLE]


@dataclass
class SLEResult:
    severity: Severity
    delay_days: int
    due_date: date


def resolve_sle(caa_score: float, rules: list[SLERule], *, from_date: date | None = None) -> SLEResult:
    """Find the SLE rule whose [caa_min, caa_max] range contains caa_score.

    Falls back to the lowest-severity rule (or a 180-day default) if no rule matches,
    so imports never fail because of an incomplete rule table.
    """
    from_date = from_date or date.today()
    matching = [r for r in rules if r.caa_min <= caa_score <= r.caa_max]
    if matching:
        rule = max(matching, key=lambda r: r.caa_min)
        return SLEResult(rule.severity, rule.delay_days, from_date + timedelta(days=rule.delay_days))

    if rules:
        rule = min(rules, key=lambda r: r.caa_min)
        return SLEResult(rule.severity, rule.delay_days, from_date + timedelta(days=rule.delay_days))

    return SLEResult(Severity.FAIBLE, 180, from_date + timedelta(days=180))
