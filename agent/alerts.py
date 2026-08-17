"""Envoi des alertes (email SMTP, webhook Slack/Teams) pour les détections triées."""

from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText

import requests

from .config import Config
from .triage import TriagedFinding

logger = logging.getLogger(__name__)

RISK_EMOJI = {"high": "🔴", "medium": "🟠", "low": "🟡"}


def format_report(domain: str, findings: list[TriagedFinding]) -> str:
    lines = [f"Surveillance typosquatting pour {domain} — {len(findings)} nouveau(x) domaine(s) détecté(s)\n"]
    for f in sorted(findings, key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.risk, 3)):
        emoji = RISK_EMOJI.get(f.risk, "⚪")
        lines.append(f"{emoji} {f.domain} — risque {f.risk}")
        lines.append(f"   {f.reason}")
        if f.raw.a_records:
            lines.append(f"   DNS: {', '.join(f.raw.a_records)}")
        if f.raw.has_certificate:
            lines.append(f"   Certificat TLS émis par: {', '.join(f.raw.certificate_issuers) or 'inconnu'}")
        if f.raw.whois_creation_date:
            lines.append(f"   WHOIS créé le: {f.raw.whois_creation_date}")
        lines.append("")
    return "\n".join(lines)


def send_email(config: Config, subject: str, body: str) -> bool:
    if not (config.smtp_host and config.alert_email_from and config.alert_email_to):
        logger.info("Configuration email incomplète, alerte email ignorée.")
        return False
    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = config.alert_email_from
    msg["To"] = ", ".join(config.alert_email_to)
    try:
        with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=config.request_timeout) as server:
            server.starttls()
            if config.smtp_user and config.smtp_password:
                server.login(config.smtp_user, config.smtp_password)
            server.sendmail(config.alert_email_from, config.alert_email_to, msg.as_string())
        return True
    except Exception as exc:
        logger.error("Envoi email échoué: %s", exc)
        return False


def send_webhook(url: str, text: str, timeout: int = 8) -> bool:
    try:
        resp = requests.post(url, json={"text": text}, timeout=timeout)
        resp.raise_for_status()
        return True
    except Exception as exc:
        logger.error("Envoi webhook échoué (%s): %s", url, exc)
        return False


def send_alerts(config: Config, findings: list[TriagedFinding]) -> None:
    if not findings:
        return
    subject = f"[Typosquatting] {len(findings)} nouveau(x) domaine(s) suspect(s) pour {config.domain}"
    body = format_report(config.domain, findings)

    sent = False
    if send_email(config, subject, body):
        sent = True
    if config.slack_webhook_url and send_webhook(config.slack_webhook_url, body, config.request_timeout):
        sent = True
    if config.teams_webhook_url and send_webhook(config.teams_webhook_url, body, config.request_timeout):
        sent = True

    if not sent:
        logger.warning("Aucun canal d'alerte configuré/opérationnel — voir %s pour le détail.", config.findings_path)
