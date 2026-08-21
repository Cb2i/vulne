"""
Informations broker PU Prime pour XAUUSD.sc.

Il n'existe pas d'API/MCP public chez PU Prime. Ce module stocke la derniere
verification MANUELLE (faite par l'utilisateur dans MT4 : Market Watch > clic
droit sur XAUUSD.sc > Specification, et sur puprime.com) et alerte si elle date
de plus de 7 jours. Ne jamais deduire ces valeurs d'un autre broker ou d'un
autre symbole (XAUUSD, XAUUSD247 sont des instruments differents).
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

STORE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "puprime_specs.json"


@dataclass
class PuPrimeSpecs:
    symbol: str
    trading_hours: str
    spread_typical: str
    leverage: str
    rollover: str
    notes: str
    verified_at_utc: str
    verified_by: str


def load_specs() -> PuPrimeSpecs | None:
    if not STORE_PATH.exists():
        return None
    with open(STORE_PATH, encoding="utf-8") as f:
        return PuPrimeSpecs(**json.load(f))


def save_specs(specs: PuPrimeSpecs) -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(asdict(specs), f, ensure_ascii=False, indent=2)


def is_stale(specs: PuPrimeSpecs | None, max_age_days: int = 7) -> bool:
    if specs is None:
        return True
    verified = datetime.fromisoformat(specs.verified_at_utc)
    age_days = (datetime.now(timezone.utc) - verified).days
    return age_days > max_age_days
