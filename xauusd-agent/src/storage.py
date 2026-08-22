"""Stockage historique minimal (SQLite) des rapports et scores quotidiens."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "history.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS daily_reports (
    date TEXT PRIMARY KEY,
    risk_score REAL,
    risk_level TEXT,
    last_close REAL,
    high REAL,
    low REAL,
    report_markdown TEXT
);
"""


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(SCHEMA)
        conn.commit()


def save_daily_report(date: str, risk_score: float, risk_level: str, last_close: float | None,
                       high: float | None, low: float | None, report_markdown: str) -> None:
    init_db()
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO daily_reports (date, risk_score, risk_level, last_close, high, low, report_markdown) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (date, risk_score, risk_level, last_close, high, low, report_markdown),
        )
        conn.commit()


def get_last_n_days(n: int = 7) -> list[dict]:
    init_db()
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM daily_reports ORDER BY date DESC LIMIT ?", (n,)
        ).fetchall()
        return [dict(r) for r in rows]
