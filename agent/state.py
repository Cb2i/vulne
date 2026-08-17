"""Persistance de l'état entre deux exécutions, pour n'alerter que sur les nouveautés."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone


def load_state(path: str) -> dict:
    if not os.path.exists(path):
        return {"known_domains": [], "last_run": None}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_state(path: str, known_domains: list[str]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    state = {
        "known_domains": sorted(known_domains),
        "last_run": datetime.now(timezone.utc).isoformat(),
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, ensure_ascii=False)
