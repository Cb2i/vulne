"""Team ownership assignment engine, matching the 'KPI' sheet semantics
(Equipes / Champ_nom d'hôtes / Champ_OS). Rules are evaluated in ascending
`priority` order; the first rule whose patterns match the asset wins.

Pattern syntax (case-insensitive):
  - "commence par <x>"  -> hostname/OS must start with <x>
  - "contient <x>" / plain text -> substring match
  - empty/None pattern  -> wildcard, always matches that field
"""
from app.models.rules import OwnershipRule

_STARTS_WITH_PREFIX = "commence par "
_CONTAINS_PREFIX = "contient "


def _matches(pattern: str | None, value: str | None) -> bool:
    if not pattern:
        return True
    if not value:
        return False
    pattern = pattern.strip().lower()
    value = value.strip().lower()
    if pattern.startswith(_STARTS_WITH_PREFIX):
        return value.startswith(pattern[len(_STARTS_WITH_PREFIX):].strip())
    if pattern.startswith(_CONTAINS_PREFIX):
        return pattern[len(_CONTAINS_PREFIX):].strip() in value
    return pattern in value


def resolve_team(*, hostname: str | None, os: str | None, rules: list[OwnershipRule]) -> int | None:
    """Return the team_id of the first active, matching rule (lowest priority number first)."""
    ordered = sorted((r for r in rules if r.active), key=lambda r: r.priority)
    for rule in ordered:
        if _matches(rule.hostname_pattern, hostname) and _matches(rule.os_pattern, os):
            return rule.team_id
    return None
