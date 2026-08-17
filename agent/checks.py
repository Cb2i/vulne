"""Vérifications d'activité d'un nom de domaine candidat.

Trois signaux indépendants, chacun tolérant aux erreurs réseau/timeout :
- résolution DNS (A/AAAA/MX)
- WHOIS (date de création, registrar)
- certificats TLS publiés (Certificate Transparency via crt.sh)
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any

import dns.resolver
import requests
import whois

logger = logging.getLogger(__name__)

CRTSH_URL = "https://crt.sh/"


@dataclass
class CandidateResult:
    domain: str
    resolves: bool = False
    a_records: list[str] = field(default_factory=list)
    has_mx: bool = False
    whois_registrar: str | None = None
    whois_creation_date: str | None = None
    has_certificate: bool = False
    certificate_issuers: list[str] = field(default_factory=list)

    @property
    def active(self) -> bool:
        return self.resolves or self.has_certificate or bool(self.whois_creation_date)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _resolve(domain: str, record_type: str, timeout: int) -> list[str]:
    try:
        answers = dns.resolver.resolve(domain, record_type, lifetime=timeout)
        return [str(rdata) for rdata in answers]
    except Exception:
        return []


def check_dns(domain: str, timeout: int = 8) -> tuple[bool, list[str], bool]:
    a_records = _resolve(domain, "A", timeout) + _resolve(domain, "AAAA", timeout)
    mx_records = _resolve(domain, "MX", timeout)
    return bool(a_records), a_records, bool(mx_records)


def check_whois(domain: str, timeout: int = 8) -> tuple[str | None, str | None]:
    try:
        record = whois.whois(domain, timeout=timeout)
    except Exception as exc:
        logger.debug("WHOIS échoué pour %s: %s", domain, exc)
        return None, None
    registrar = record.get("registrar") if isinstance(record, dict) else getattr(record, "registrar", None)
    creation = record.get("creation_date") if isinstance(record, dict) else getattr(record, "creation_date", None)
    if isinstance(creation, list):
        creation = creation[0] if creation else None
    return (str(registrar) if registrar else None, str(creation) if creation else None)


def check_certificate_transparency(domain: str, timeout: int = 8) -> tuple[bool, list[str]]:
    try:
        resp = requests.get(
            CRTSH_URL,
            params={"q": domain, "output": "json"},
            timeout=timeout,
            headers={"User-Agent": "typosquat-agent/1.0"},
        )
        resp.raise_for_status()
        entries = resp.json()
    except Exception as exc:
        logger.debug("crt.sh échoué pour %s: %s", domain, exc)
        return False, []
    issuers = sorted({entry.get("issuer_name", "") for entry in entries if entry.get("issuer_name")})
    return bool(entries), issuers


def check_candidate(domain: str, timeout: int = 8) -> CandidateResult:
    resolves, a_records, has_mx = check_dns(domain, timeout)
    result = CandidateResult(domain=domain, resolves=resolves, a_records=a_records, has_mx=has_mx)

    # Évite les lookups WHOIS/CT coûteux pour les domaines qui ne résolvent
    # même pas — la grande majorité des ~400 candidats générés.
    if resolves:
        registrar, creation_date = check_whois(domain, timeout)
        result.whois_registrar = registrar
        result.whois_creation_date = creation_date
        has_cert, issuers = check_certificate_transparency(domain, timeout)
        result.has_certificate = has_cert
        result.certificate_issuers = issuers
    return result
