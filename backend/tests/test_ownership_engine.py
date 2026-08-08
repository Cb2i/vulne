from app.models.rules import OwnershipRule
from app.rules.ownership.engine import resolve_team


def _rule(id_, team_id, hostname_pattern=None, os_pattern=None, priority=100, active=True):
    r = OwnershipRule(team_id=team_id, hostname_pattern=hostname_pattern, os_pattern=os_pattern, priority=priority, active=active)
    r.id = id_
    return r


def test_starts_with_pattern_matches():
    rules = [_rule(1, team_id=2, hostname_pattern="commence par q2")]
    assert resolve_team(hostname="q212675", os="Windows", rules=rules) == 2
    assert resolve_team(hostname="apji-jy3jcb8tio", os="Windows", rules=rules) is None


def test_first_matching_rule_by_priority_wins():
    rules = [
        _rule(1, team_id=1, hostname_pattern="commence par vm-", priority=10),
        _rule(2, team_id=2, hostname_pattern=None, priority=100),  # wildcard fallback
    ]
    assert resolve_team(hostname="vm-caa-int01", os=None, rules=rules) == 1
    assert resolve_team(hostname="other-host", os=None, rules=rules) == 2


def test_inactive_rules_are_ignored():
    rules = [_rule(1, team_id=1, hostname_pattern="commence par q2", active=False)]
    assert resolve_team(hostname="q212675", os=None, rules=rules) is None
