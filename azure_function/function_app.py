"""Azure Function (modèle Python v2) exécutant le scan anti-typosquatting sur un timer.

Déploiement : la commande `func azure functionapp publish` (ou le pipeline
CI/CD Azure) doit packager ce dossier avec le dossier `agent/` du dépôt à sa
racine — voir README.md pour les deux options possibles.

Configuration : mêmes variables d'environnement que le script CLI
(agent/config.py), à définir dans les "Application settings" de la Function
App (ou via Key Vault references pour les secrets).
"""

from __future__ import annotations

import logging
import os
import sys

import azure.functions as func

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent.main import run_scan  # noqa: E402

app = func.FunctionApp()

logger = logging.getLogger("typosquat-agent.azure")


@app.timer_trigger(schedule="0 0 6 * * *", arg_name="timer", run_on_startup=False)
def typosquat_scan(timer: func.TimerRequest) -> None:
    if timer.past_due:
        logger.warning("La fonction s'exécute en retard sur son planning.")
    findings = run_scan()
    logger.info("Scan terminé : %d domaine(s) actif(s) au total.", len(findings))
