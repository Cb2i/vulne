"""Exception (risk acceptance) matching engine."""
from datetime import date

from app.models.exception import ExceptionRecord

_CONTAINS_PREFIX = "contient "


def _matches_text(pattern: str | None, value: str | None) -> bool:
    if not pattern:
        return True
    if not value:
        return False
    pattern = pattern.strip().lower()
    value = value.strip().lower()
    if pattern.startswith(_CONTAINS_PREFIX):
        return pattern[len(_CONTAINS_PREFIX):].strip() in value
    return pattern in value


def find_matching_exception(
    *,
    plugin_name: str | None,
    cve: str | None,
    hostname: str | None,
    exceptions: list[ExceptionRecord],
    today: date | None = None,
) -> ExceptionRecord | None:
    """Return the first active, non-expired exception matching this finding, if any."""
    today = today or date.today()
    for exc in exceptions:
        if exc.status.value != "active":
            continue
        if exc.expires_at and exc.expires_at < today:
            continue
        vuln_match = _matches_text(exc.vulnerability_match, plugin_name) or _matches_text(
            exc.vulnerability_match, cve
        )
        if not vuln_match:
            continue
        if not _matches_text(exc.hostname_pattern, hostname):
            continue
        return exc
    return None
