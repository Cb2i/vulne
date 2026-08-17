"""Point d'entrée CLI de l'agent de surveillance anti-typosquatting.

Usage:
    python -m agent.main [--domain example.com] [--dry-run]

Variables d'environnement attendues : voir agent/config.py et README.md.
"""

from __future__ import annotations

import argparse
import json
import logging
import os

from .alerts import send_alerts
from .checks import check_candidate
from .config import load_config
from .generator import generate_candidates
from .state import load_state, save_state
from .triage import triage_findings

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("typosquat-agent")


def run_scan(dry_run: bool = False) -> list[dict]:
    config = load_config()
    if config.is_placeholder_domain:
        logger.warning(
            "TARGET_DOMAIN n'est pas configuré (utilise le placeholder '%s'). "
            "Définissez la variable d'environnement TARGET_DOMAIN.",
            config.domain,
        )

    candidates = generate_candidates(config.domain, config.brand_keywords, config.max_candidates)
    logger.info("Vérification de %d domaines candidats pour %s", len(candidates), config.domain)

    results = [check_candidate(c, config.request_timeout) for c in candidates]
    active_results = [r for r in results if r.active]
    logger.info("%d domaine(s) actif(s) détecté(s)", len(active_results))

    previous_state = load_state(config.state_path)
    known = set(previous_state.get("known_domains", []))
    new_findings = [r for r in active_results if r.domain not in known]
    logger.info("%d nouvelle(s) détection(s) depuis la dernière exécution", len(new_findings))

    if new_findings and not dry_run:
        triaged = triage_findings(new_findings, config.anthropic_api_key)
        send_alerts(config, triaged)

    if not dry_run:
        save_state(config.state_path, [r.domain for r in active_results])
        os.makedirs(os.path.dirname(config.findings_path) or ".", exist_ok=True)
        with open(config.findings_path, "w", encoding="utf-8") as fh:
            json.dump([r.to_dict() for r in active_results], fh, indent=2, ensure_ascii=False)

    return [r.to_dict() for r in active_results]


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent de surveillance anti-typosquatting")
    parser.add_argument("--domain", help="Surcharge TARGET_DOMAIN pour cette exécution")
    parser.add_argument("--dry-run", action="store_true", help="N'envoie aucune alerte, n'écrit aucun état")
    args = parser.parse_args()

    if args.domain:
        os.environ["TARGET_DOMAIN"] = args.domain

    run_scan(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
