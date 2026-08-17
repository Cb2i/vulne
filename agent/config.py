"""Chargement de la configuration de l'agent depuis les variables d'environnement."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

PLACEHOLDER_DOMAIN = "example.com"


@dataclass
class Config:
    domain: str
    brand_keywords: list[str] = field(default_factory=list)
    anthropic_api_key: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    alert_email_from: str | None = None
    alert_email_to: list[str] = field(default_factory=list)
    slack_webhook_url: str | None = None
    teams_webhook_url: str | None = None
    state_path: str = "agent/state.json"
    findings_path: str = "agent/findings.json"
    max_candidates: int = 400
    request_timeout: int = 8

    @property
    def is_placeholder_domain(self) -> bool:
        return self.domain == PLACEHOLDER_DOMAIN


def _split_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def load_config() -> Config:
    return Config(
        domain=os.environ.get("TARGET_DOMAIN", PLACEHOLDER_DOMAIN).lower().strip(),
        brand_keywords=_split_list(os.environ.get("BRAND_KEYWORDS")),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
        smtp_host=os.environ.get("SMTP_HOST") or None,
        smtp_port=int(os.environ.get("SMTP_PORT", "587")),
        smtp_user=os.environ.get("SMTP_USER") or None,
        smtp_password=os.environ.get("SMTP_PASSWORD") or None,
        alert_email_from=os.environ.get("ALERT_EMAIL_FROM") or None,
        alert_email_to=_split_list(os.environ.get("ALERT_EMAIL_TO")),
        slack_webhook_url=os.environ.get("SLACK_WEBHOOK_URL") or None,
        teams_webhook_url=os.environ.get("TEAMS_WEBHOOK_URL") or None,
        state_path=os.environ.get("AGENT_STATE_PATH", "agent/state.json"),
        findings_path=os.environ.get("AGENT_FINDINGS_PATH", "agent/findings.json"),
    )
