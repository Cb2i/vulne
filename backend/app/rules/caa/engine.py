"""CAA (Contextual Asset Adjustment) scoring engine.

Computes a 0-10 risk-adjusted score from the raw CVSS score plus asset context
(network exposure, business criticality) and real-world exploitability, using
configurable weights (app.models.rules.CAAConfig). This generalizes the
adjustment logic first prototyped in vuln_manager.html and mirrors the
"Score CAA" column produced by the organization's enriched Tenable workbook.
"""
from dataclasses import dataclass, field

from app.models.rules import CAAConfig

EXPOSITION_NORMALIZATION = {
    "internet": "internet",
    "dmz": "dmz",
    "internal": "internal",
    "interne": "internal",
    "airgapped": "airgapped",
    "air-gapped": "airgapped",
}

CRITICITE_NORMALIZATION = {
    "critical": "critical",
    "critique": "critical",
    "high": "high",
    "haute": "high",
    "élevée": "high",
    "medium": "medium",
    "moyenne": "medium",
    "low": "low",
    "faible": "low",
}


@dataclass
class CAAAdjustment:
    reason: str
    delta: float


@dataclass
class CAAResult:
    cvss: float
    caa_score: float
    adjustments: list[CAAAdjustment] = field(default_factory=list)


def _normalize(value: str | None, mapping: dict[str, str], default: str) -> str:
    if not value:
        return default
    return mapping.get(value.strip().lower(), default)


def compute_caa_score(
    *,
    cvss: float | None,
    exposition: str | None,
    criticite: str | None,
    exploitable: bool,
    config: CAAConfig,
) -> CAAResult:
    """Pure function: given raw inputs and an active CAAConfig, return the adjusted score."""
    base = float(cvss) if cvss is not None else 0.0
    score = base
    adjustments: list[CAAAdjustment] = []

    exposition_key = _normalize(exposition, EXPOSITION_NORMALIZATION, "internal")
    exposition_weight = {
        "internet": config.weight_exposition_internet,
        "dmz": config.weight_exposition_dmz,
        "internal": config.weight_exposition_internal,
        "airgapped": config.weight_exposition_airgapped,
    }[exposition_key]
    score += exposition_weight
    adjustments.append(CAAAdjustment(f"Exposition: {exposition or 'Internal'}", exposition_weight))

    criticite_key = _normalize(criticite, CRITICITE_NORMALIZATION, "medium")
    criticite_weight = {
        "critical": config.weight_criticite_critical,
        "high": config.weight_criticite_high,
        "medium": config.weight_criticite_medium,
        "low": config.weight_criticite_low,
    }[criticite_key]
    score += criticite_weight
    adjustments.append(CAAAdjustment(f"Criticité de l'actif: {criticite or 'Medium'}", criticite_weight))

    if exploitable:
        score += config.weight_exploitable
        adjustments.append(CAAAdjustment("Exploitabilité confirmée", config.weight_exploitable))

    divisor = config.normalization_divisor or 1.0
    score = score / divisor
    score = max(0.0, min(10.0, score))
    score = round(score, 2)

    return CAAResult(cvss=base, caa_score=score, adjustments=adjustments)
