"""Chargement de la configuration (config/config.yaml + .env)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    load_dotenv(ROOT / ".env")
    cfg_path = Path(path) if path else ROOT / "config" / "config.yaml"
    if not cfg_path.exists():
        cfg_path = ROOT / "config" / "config.example.yaml"
    with open(cfg_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_secret(name: str) -> str | None:
    value = os.environ.get(name)
    return value if value else None
