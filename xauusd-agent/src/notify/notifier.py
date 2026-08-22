"""Notification du rapport genere : fichier local systematique + webhook/email optionnels."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import httpx

from ..config import get_secret

REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "reports_out"


def save_to_file(report_markdown: str, kind: str = "daily") -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{kind}_{datetime.now().strftime('%Y-%m-%d_%H%M')}.md"
    path = REPORTS_DIR / filename
    path.write_text(report_markdown, encoding="utf-8")
    return path


def send_webhook(report_markdown: str) -> bool:
    url = get_secret("NOTIFY_WEBHOOK_URL")
    if not url:
        return False
    try:
        resp = httpx.post(url, json={"text": report_markdown}, timeout=10)
        return resp.status_code < 400
    except httpx.HTTPError:
        return False


def dispatch(report_markdown: str, kind: str = "daily") -> Path:
    path = save_to_file(report_markdown, kind)
    send_webhook(report_markdown)
    return path
