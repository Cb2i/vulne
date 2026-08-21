"""
Assemble les donnees collectees/analysees en contexte de template pour le
rapport quotidien, puis rend le Markdown final. Toute valeur manquante est
explicitement affichee comme non disponible (jamais inventee).
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ..analysis import levels as levels_mod
from ..analysis import sessions as sessions_mod
from ..analysis.technical import compute_all
from ..collectors.economic_calendar import CalendarEvent, get_calendar, is_high_impact
from ..collectors.fred_client import get_us_yields
from ..collectors.market_data import get_market_snapshot
from ..collectors.news import NewsItem
from ..risk.risk_engine import compute_risk_score
from ..risk.timeline import build_risk_timeline
from ..timezones import now_montreal
from .formatting import NA, fmt_list, fmt_num, strip_forbidden_chars

TEMPLATE_DIR = Path(__file__).parent / "templates"


def _trend_label(ema20: float | None, ema50: float | None, last_close: float | None) -> tuple[str, str]:
    if ema20 is None or ema50 is None or last_close is None:
        return "⚪", NA
    if last_close > ema20 > ema50:
        return "🟢", "Haussiere"
    if last_close < ema20 < ema50:
        return "🔴", "Baissiere"
    return "🟠", "Indecise / range"


def build_daily_context(symbol: str = "XAU/USD") -> dict:
    now = now_montreal()

    tf_data = {}
    for tf in ["D1", "H4", "H1", "M15"]:
        snapshot = get_market_snapshot(symbol, tf)
        indicators = compute_all(snapshot.candles) if snapshot else compute_all([])
        tf_data[tf] = {"snapshot": snapshot, "indicators": indicators}

    h1_ind = tf_data["H1"]["indicators"]
    trend_emoji, trend_label = _trend_label(h1_ind["ema20"], h1_ind["ema50"], h1_ind["last_close"])

    daily_candles = tf_data["D1"]["snapshot"].candles if tf_data["D1"]["snapshot"] else []
    h1_candles = tf_data["H1"]["snapshot"].candles if tf_data["H1"]["snapshot"] else []
    pdh_pdl = levels_mod.previous_day_high_low(daily_candles)
    weekly = levels_mod.weekly_high_low(daily_candles)
    sr = levels_mod.support_resistance_from_swings(h1_candles)
    psych = levels_mod.psychological_levels(h1_ind["last_close"])

    sessions = sessions_mod.build_sessions(now)

    calendar_events: list[CalendarEvent] = get_calendar()
    events_montreal = []
    for ev in calendar_events:
        try:
            dt = datetime.fromisoformat(ev.datetime_utc.replace("Z", "+00:00")).astimezone(now.tzinfo)
            events_montreal.append((dt, ev))
        except ValueError:
            continue

    major_upcoming = sorted(
        [(dt, ev) for dt, ev in events_montreal if is_high_impact(ev.event) and dt >= now],
        key=lambda x: x[0],
    )
    next_event = major_upcoming[0] if major_upcoming else None

    yields = get_us_yields()
    us10y = yields["US10Y"]
    us02y = yields["US02Y"]

    risk = compute_risk_score(
        next_major_event_dt=next_event[0] if next_event else None,
        now=now,
        is_major_event=bool(next_event),
        atr14=h1_ind["atr14"],
        atr_avg20=None,  # necessite un historique ATR non calcule dans ce mode simple
        m15_amplitude_ratio=None,
        in_session_overlap=False,
        in_single_session=False,
        dxy_change_pct=None,
        us10y_change_bp=None,
        confirmed_major_news=False,
    )

    vol_emoji, vol_label = ("🟢", "Faible")
    if h1_ind["atr14"] is not None and h1_ind["last_close"]:
        atr_pct = h1_ind["atr14"] / h1_ind["last_close"] * 100
        if atr_pct > 0.6:
            vol_emoji, vol_label = "🔴", "Elevee"
        elif atr_pct > 0.35:
            vol_emoji, vol_label = "🟠", "Moderee"
    risk.vol_emoji, risk.vol_label = vol_emoji, vol_label  # type: ignore[attr-defined]

    timeline = build_risk_timeline(
        events_montreal=[(dt, ev) for dt, ev in events_montreal],
        day_start=now.replace(hour=0, minute=0, second=0, microsecond=0),
        day_end=now.replace(hour=23, minute=59, second=0, microsecond=0),
    )

    context = {
        "risk": {
            "total_score": risk.total_score,
            "emoji": risk.emoji,
            "level": risk.level,
            "vol_emoji": vol_emoji,
            "vol_label": vol_label,
        },
        "h1": {
            "trend_emoji": trend_emoji,
            "trend_label": trend_label,
            "ema20": fmt_num(h1_ind["ema20"]),
            "ema50": fmt_num(h1_ind["ema50"]),
            "ema200": fmt_num(h1_ind["ema200"]),
            "macd": (
                f"MACD {fmt_num(h1_ind['macd']['macd'])} / Signal {fmt_num(h1_ind['macd']['signal'])} / "
                f"Hist {fmt_num(h1_ind['macd']['histogram'])}"
                if h1_ind["macd"]
                else NA
            ),
        },
        "next_event": {
            "name": next_event[1].event if next_event else None,
            "time_montreal": next_event[0].strftime("%H:%M") if next_event else None,
        },
        "current_window": {"range": "a determiner selon timeline", "reason": "voir section Risk Timeline"},
        "risk_summary_lines": [
            {"emoji": e.level, "range": f"{e.start_montreal}-{e.end_montreal}", "label": e.reason}
            for e in timeline
        ],
        "executive_summary": (
            f"Tendance H1 {trend_label.lower() if trend_label != NA else NA}, "
            f"risque du jour {risk.level} ({risk.total_score}/10). {risk.explanation()}"
        ),
        "timeframes": [
            {
                "name": tf,
                "trend": _trend_label(d["indicators"]["ema20"], d["indicators"]["ema50"], d["indicators"]["last_close"])[1],
                "structure": NA,
                "rsi": fmt_num(d["indicators"]["rsi14"]),
                "atr": fmt_num(d["indicators"]["atr14"]),
            }
            for tf, d in tf_data.items()
        ],
        "levels": {
            "previous_day_high": fmt_num(pdh_pdl["previous_day_high"]),
            "previous_day_low": fmt_num(pdh_pdl["previous_day_low"]),
            "weekly_high": fmt_num(weekly["weekly_high"]),
            "weekly_low": fmt_num(weekly["weekly_low"]),
            "resistances": fmt_list(sr["resistances"]),
            "supports": fmt_list(sr["supports"]),
            "psychological": fmt_list(psych),
        },
        "sessions": sessions,
        "calendar": [
            {
                "time": dt.strftime("%H:%M"),
                "name": ev.event,
                "importance": ev.importance,
                "consensus": ev.consensus or NA,
                "previous": ev.previous or NA,
                "actual": ev.actual or "en attente",
                "impact": "a evaluer a la publication",
            }
            for dt, ev in sorted(events_montreal, key=lambda x: x[0])
        ],
        "macro": {
            "dxy": NA,
            "us10y": fmt_num(us10y.value, 2, "%") if us10y else NA,
            "us10y_date": us10y.date if us10y else NA,
            "us02y": fmt_num(us02y.value, 2, "%") if us02y else NA,
            "us02y_date": us02y.date if us02y else NA,
            "context_note": (
                "USD/rendements en baisse conjugues sont historiquement plutot favorables a l'or, "
                "mais chaque contexte doit etre analyse independamment."
            ),
        },
        "news": [],
        "timeline": [
            {"start_montreal": e.start_montreal, "end_montreal": e.end_montreal, "level": e.level, "reason": e.reason}
            for e in timeline
        ],
        "points_to_monitor": [
            "Confirmer la normalisation de la volatilite avant de considerer une fenetre rouge comme terminee.",
            "Verifier les specifications XAUUSD.sc dans MT4 si la derniere verification date de plus de 7 jours.",
        ],
        "robot": {
            "stop_guidance": (
                f"desactiver au plus tard {(next_event[0]).strftime('%H:%M') if next_event else NA} moins 15 minutes "
                "si un evenement majeur est identifie dans la timeline (fenetre 🔴)."
                if next_event
                else "aucun arret specifique requis selon les evenements actuellement identifies."
            ),
            "restart_guidance": (
                "reactiver seulement lorsque la section Risk Timeline repasse a 🟢 ET que l'ATR/amplitude M15 "
                "confirment une normalisation (voir section 9), jamais a une heure fixe par defaut."
            ),
        },
        "sources": [
            "Twelve Data (OHLC/indicateurs)" if tf_data["H1"]["snapshot"] else "Twelve Data : non disponible (cle API absente ou echec)",
            "Trading Economics (calendrier)" if calendar_events else "Calendrier economique : non disponible",
            f"FRED (US10Y {us10y.date if us10y else NA}, US02Y {us02y.date if us02y else NA})",
        ],
        "generated_at": now.isoformat(),
    }
    return context


def render_daily_report(context: dict | None = None) -> str:
    context = context or build_daily_context()
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template("daily_report.md.j2")
    return strip_forbidden_chars(template.render(**context))
