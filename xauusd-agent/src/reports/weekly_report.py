"""
Rapport hebdomadaire : synthese de la semaine ecoulee (a partir de l'historique
stocke par le rapport quotidien) + carte de risque de la semaine suivante
(a partir du calendrier reel). Aucune donnee n'est extrapolee au-dela de ce qui
est disponible : les champs sans historique suffisant affichent NA.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ..collectors.economic_calendar import CalendarEvent, get_calendar, is_high_impact
from ..collectors.fred_client import get_us_yields
from ..storage import get_last_n_days
from ..timezones import now_montreal
from .formatting import INVESTING_COM_REFS, NA, strip_forbidden_chars

TEMPLATE_DIR = Path(__file__).parent / "templates"
DAY_NAMES_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


def build_weekly_context() -> dict:
    now = now_montreal()
    history = get_last_n_days(5)

    if history:
        closes = [h["last_close"] for h in history if h["last_close"] is not None]
        highs = [h["high"] for h in history if h["high"] is not None]
        lows = [h["low"] for h in history if h["low"] is not None]
        performance_pct = (
            round((closes[0] - closes[-1]) / closes[-1] * 100, 2) if len(closes) >= 2 and closes[-1] else None
        )
        week_high = max(highs) if highs else None
        week_low = min(lows) if lows else None
    else:
        performance_pct = week_high = week_low = None

    yields = get_us_yields()
    us10y, us02y = yields["US10Y"], yields["US02Y"]

    start_next_week = now + timedelta(days=(7 - now.weekday()))
    end_next_week = start_next_week + timedelta(days=6)
    events = get_calendar(start=start_next_week.strftime("%Y-%m-%d"), end=end_next_week.strftime("%Y-%m-%d"))

    next_week_map: dict[str, list[CalendarEvent]] = {name: [] for name in DAY_NAMES_FR}
    for ev in events:
        try:
            dt = datetime.fromisoformat(ev.datetime_utc.replace("Z", "+00:00")).astimezone(now.tzinfo)
        except ValueError:
            continue
        next_week_map[DAY_NAMES_FR[dt.weekday()]].append((dt, ev))  # type: ignore[arg-type]

    next_week_rows = []
    for day_name in DAY_NAMES_FR:
        day_events = sorted(next_week_map[day_name], key=lambda x: x[0])  # type: ignore[arg-type]
        major = [(dt, ev) for dt, ev in day_events if is_high_impact(ev.event)]
        if major:
            dt, ev = major[0]
            risk_emoji = "🔴" if len(major) > 0 else "🟢"
            next_week_rows.append({"name": day_name, "risk_emoji": risk_emoji, "event": ev.event, "time": dt.strftime("%H:%M")})
        else:
            next_week_rows.append({"name": day_name, "risk_emoji": "🟢", "event": "Aucun evenement majeur identifie", "time": NA})

    context = {
        "week": {
            "start": (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d"),
            "end": now.strftime("%Y-%m-%d"),
            "performance_pct": performance_pct if performance_pct is not None else NA,
            "high": week_high if week_high is not None else NA,
            "low": week_low if week_low is not None else NA,
            "range": (round(week_high - week_low, 2) if week_high is not None and week_low is not None else NA),
            "trend_summary": NA if not history else "voir historique des rapports quotidiens de la semaine",
            "volatility_summary": NA,
            "dxy_summary": NA,
            "us10y_summary": f"{us10y.value}% au {us10y.date}" if us10y else NA,
            "us02y_summary": f"{us02y.value}% au {us02y.date}" if us02y else NA,
            "market_moving_events": [],
            "resistances": NA,
            "supports": NA,
        },
        "next_week": next_week_rows,
        "robot": {
            "weekly_guidance": (
                "Desactiver le robot 15 minutes avant chaque case 🔴 du tableau ci-dessus et le reactiver "
                "seulement apres confirmation de normalisation de la volatilite (ATR/amplitude M15), jamais "
                "automatiquement a heure fixe."
            )
        },
        "sources": [
            "Historique local des rapports quotidiens (data/history.db)",
            "Trading Economics (calendrier)" if events else "Calendrier economique : non disponible",
            f"FRED (US10Y {us10y.date if us10y else NA}, US02Y {us02y.date if us02y else NA})",
            *INVESTING_COM_REFS,
        ],
    }
    return context


def render_weekly_report(context: dict | None = None) -> str:
    context = context or build_weekly_context()
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template("weekly_report.md.j2")
    return strip_forbidden_chars(template.render(**context))
