"""Triage des détections : scoring de risque + message d'alerte lisible.

Deux modes :
- IA (si ANTHROPIC_API_KEY défini) : Claude évalue chaque domaine actif et
  rédige une note de risque + une recommandation.
- Règles (fallback) : scoring déterministe basé sur les signaux collectés.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from .checks import CandidateResult

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = """Tu es un analyste en sécurité spécialisé dans la détection de typosquatting.
On te donne une liste de domaines suspects ressemblant à un domaine de marque légitime, avec
des signaux techniques (DNS, WHOIS, certificats TLS observés).
Pour chaque domaine, évalue le risque qu'il soit utilisé pour du phishing ou de l'usurpation de
marque, et réponds UNIQUEMENT avec un tableau JSON de la forme :
[{"domain": "...", "risk": "low|medium|high", "reason": "..."}]
Le champ "reason" doit être une phrase courte en français expliquant le verdict."""


@dataclass
class TriagedFinding:
    domain: str
    risk: str
    reason: str
    raw: CandidateResult


def rule_based_triage(findings: list[CandidateResult]) -> list[TriagedFinding]:
    triaged = []
    for f in findings:
        if f.has_certificate and f.resolves:
            risk, reason = "high", "Domaine résolu et certificat TLS émis : site probablement en ligne."
        elif f.resolves and f.has_mx:
            risk, reason = "high", "Domaine résolu avec enregistrement MX : peut être utilisé pour envoyer des emails de phishing."
        elif f.resolves:
            risk, reason = "medium", "Domaine résolu mais sans certificat ni MX détecté."
        elif f.whois_creation_date:
            risk, reason = "low", "Domaine enregistré (WHOIS) mais ne résout pas encore."
        else:
            risk, reason = "low", "Signal faible."
        triaged.append(TriagedFinding(domain=f.domain, risk=risk, reason=reason, raw=f))
    return triaged


def ai_triage(findings: list[CandidateResult], api_key: str) -> list[TriagedFinding]:
    try:
        import anthropic
    except ImportError:
        logger.warning("Le paquet 'anthropic' n'est pas installé, bascule sur le triage par règles.")
        return rule_based_triage(findings)

    client = anthropic.Anthropic(api_key=api_key)
    payload = [f.to_dict() for f in findings]

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        verdicts = json.loads(text)
    except Exception as exc:
        logger.warning("Triage IA échoué (%s), bascule sur le triage par règles.", exc)
        return rule_based_triage(findings)

    by_domain = {f.domain: f for f in findings}
    triaged = []
    for verdict in verdicts:
        raw = by_domain.get(verdict.get("domain"))
        if raw is None:
            continue
        triaged.append(
            TriagedFinding(
                domain=verdict["domain"],
                risk=verdict.get("risk", "medium"),
                reason=verdict.get("reason", ""),
                raw=raw,
            )
        )
    # S'assure qu'aucune détection n'est perdue si l'IA en a omis.
    covered = {t.domain for t in triaged}
    for f in findings:
        if f.domain not in covered:
            triaged.extend(rule_based_triage([f]))
    return triaged


def triage_findings(findings: list[CandidateResult], api_key: str | None) -> list[TriagedFinding]:
    if not findings:
        return []
    if api_key:
        return ai_triage(findings, api_key)
    return rule_based_triage(findings)
