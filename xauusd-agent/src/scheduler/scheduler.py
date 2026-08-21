"""
Planification : lundi-vendredi 06:30, dimanche 10:00 (rapport quotidien), et
vendredi (rapport hebdomadaire en plus du quotidien). Toutes les heures sont
exprimees en America/Montreal ; APScheduler + zoneinfo gerent le passage
EST/EDT automatiquement (pas de decalage fixe).
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from ..config import load_config
from ..notify.notifier import dispatch
from ..reports.daily_report import render_daily_report
from ..reports.weekly_report import render_weekly_report
from ..timezones import MONTREAL

logger = logging.getLogger("xauusd_agent.scheduler")


def run_daily() -> None:
    try:
        report = render_daily_report()
        path = dispatch(report, "daily")
        logger.info("Rapport quotidien genere : %s", path)
    except Exception:
        logger.exception("Echec de generation du rapport quotidien")


def run_weekly() -> None:
    try:
        report = render_weekly_report()
        path = dispatch(report, "weekly")
        logger.info("Rapport hebdomadaire genere : %s", path)
    except Exception:
        logger.exception("Echec de generation du rapport hebdomadaire")


def start_scheduler() -> None:
    load_config()
    scheduler = BlockingScheduler(timezone=MONTREAL)

    scheduler.add_job(run_daily, CronTrigger(day_of_week="mon-fri", hour=6, minute=30, timezone=MONTREAL), id="daily_weekday")
    scheduler.add_job(run_daily, CronTrigger(day_of_week="sun", hour=10, minute=0, timezone=MONTREAL), id="daily_sunday")
    scheduler.add_job(run_weekly, CronTrigger(day_of_week="fri", hour=6, minute=35, timezone=MONTREAL), id="weekly_friday")

    logger.info("Scheduler demarre (America/Montreal, DST auto).")
    scheduler.start()
