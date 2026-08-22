"""
Point d'entree CLI.

Usage :
    python main.py daily      -> genere et sauvegarde le rapport quotidien maintenant
    python main.py weekly     -> genere et sauvegarde le rapport hebdomadaire maintenant
    python main.py schedule   -> demarre le scheduler (lun-ven 06:30, dim 10:00, ven weekly)
"""
from __future__ import annotations

import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    # Charge .env (cles API) avant toute commande : daily/weekly appellent les
    # collecteurs directement, sans passer par start_scheduler(), qui etait le
    # seul endroit a charger .env auparavant.
    from src.config import load_config

    load_config()

    command = sys.argv[1]

    if command == "daily":
        from src.notify.notifier import dispatch
        from src.reports.daily_report import render_daily_report

        report = render_daily_report()
        path = dispatch(report, "daily")
        print(report)
        print(f"\nRapport sauvegarde : {path}")
    elif command == "weekly":
        from src.notify.notifier import dispatch
        from src.reports.weekly_report import render_weekly_report

        report = render_weekly_report()
        path = dispatch(report, "weekly")
        print(report)
        print(f"\nRapport sauvegarde : {path}")
    elif command == "schedule":
        from src.scheduler.scheduler import start_scheduler

        start_scheduler()
    else:
        print(f"Commande inconnue : {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
