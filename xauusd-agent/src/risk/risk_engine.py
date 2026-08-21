"""
Risk Engine : score 0-10 et classification 🟢/🟠/🔴, methodologie documentee
dans ARCHITECTURE.md section 5. Chaque facteur est explicite (jamais une boite
noire) pour que le rapport puisse justifier le score.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

MAJOR_EVENTS = (
    "cpi", "core cpi", "ppi", "pce", "core pce", "nonfarm payrolls", "nfp",
    "fomc", "fed interest rate", "powell", "gdp",
)


@dataclass
class RiskFactor:
    name: str
    score: float
    max_score: float
    reason: str


@dataclass
class RiskAssessment:
    total_score: float
    level: str  # "faible" / "modere" / "eleve" / "exceptionnel"
    emoji: str
    factors: list[RiskFactor] = field(default_factory=list)

    def explanation(self) -> str:
        parts = [f"{f.name}: {f.score}/{f.max_score} ({f.reason})" for f in self.factors]
        return " | ".join(parts)


def _event_proximity_score(next_event_dt: datetime | None, now: datetime, is_major: bool) -> RiskFactor:
    if next_event_dt is None or not is_major:
        return RiskFactor("Proximite evenement macro", 0, 4, "aucun evenement majeur identifie")
    delta = next_event_dt - now
    if delta <= timedelta(0):
        return RiskFactor("Proximite evenement macro", 4, 4, "evenement majeur en cours/tres recent")
    minutes = delta.total_seconds() / 60
    if minutes <= 60:
        return RiskFactor("Proximite evenement macro", 4, 4, f"evenement majeur dans {int(minutes)} min")
    if minutes <= 120:
        return RiskFactor("Proximite evenement macro", 2, 4, f"evenement majeur dans {int(minutes)} min")
    if minutes <= 1440:
        return RiskFactor("Proximite evenement macro", 1, 4, "evenement majeur plus tard dans la journee")
    return RiskFactor("Proximite evenement macro", 0, 4, "aucun evenement majeur proche")


def _atr_score(atr14: float | None, atr_avg20: float | None) -> RiskFactor:
    if atr14 is None or atr_avg20 is None or atr_avg20 == 0:
        return RiskFactor("Volatilite ATR14 H1", 0, 2, "donnee non disponible / non verifiable")
    ratio = atr14 / atr_avg20
    if ratio > 1.5:
        return RiskFactor("Volatilite ATR14 H1", 2, 2, f"ATR a {ratio:.2f}x la moyenne 20 jours")
    if ratio > 1.2:
        return RiskFactor("Volatilite ATR14 H1", 1, 2, f"ATR a {ratio:.2f}x la moyenne 20 jours")
    return RiskFactor("Volatilite ATR14 H1", 0, 2, f"ATR proche de la normale ({ratio:.2f}x)")


def _m15_amplitude_score(m15_ratio: float | None) -> RiskFactor:
    if m15_ratio is None:
        return RiskFactor("Amplitude M15 recente", 0, 1, "donnee non disponible / non verifiable")
    if m15_ratio > 2.0:
        return RiskFactor("Amplitude M15 recente", 1, 1, f"bougies M15 recentes a {m15_ratio:.2f}x la moyenne")
    return RiskFactor("Amplitude M15 recente", 0, 1, "amplitude M15 dans la norme")


def _session_score(in_overlap: bool, in_single_session: bool) -> RiskFactor:
    if in_overlap:
        return RiskFactor("Session/chevauchement", 1, 1, "chevauchement Londres/New York")
    if in_single_session:
        return RiskFactor("Session/chevauchement", 0.5, 1, "session Londres ou New York active")
    return RiskFactor("Session/chevauchement", 0, 1, "session Asie ou hors session principale")


def _dxy_yields_score(dxy_change_pct: float | None, us10y_change_bp: float | None) -> RiskFactor:
    if dxy_change_pct is None and us10y_change_bp is None:
        return RiskFactor("DXY / rendements US", 0, 1, "donnee non disponible / non verifiable")
    moved = (dxy_change_pct is not None and abs(dxy_change_pct) > 0.5) or (
        us10y_change_bp is not None and abs(us10y_change_bp) > 10
    )
    if moved:
        return RiskFactor("DXY / rendements US", 1, 1, "mouvement notable DXY ou US10Y sur la journee")
    return RiskFactor("DXY / rendements US", 0, 1, "DXY et rendements US stables")


def _news_score(confirmed_major_news: bool) -> RiskFactor:
    if confirmed_major_news:
        return RiskFactor("Actualite/geopolitique confirmee", 1, 1, "nouvelle majeure confirmee non digeree")
    return RiskFactor("Actualite/geopolitique confirmee", 0, 1, "aucune nouvelle majeure confirmee en attente")


def compute_risk_score(
    *,
    next_major_event_dt: datetime | None,
    now: datetime,
    is_major_event: bool = True,
    atr14: float | None = None,
    atr_avg20: float | None = None,
    m15_amplitude_ratio: float | None = None,
    in_session_overlap: bool = False,
    in_single_session: bool = False,
    dxy_change_pct: float | None = None,
    us10y_change_bp: float | None = None,
    confirmed_major_news: bool = False,
) -> RiskAssessment:
    factors = [
        _event_proximity_score(next_major_event_dt, now, is_major_event),
        _atr_score(atr14, atr_avg20),
        _m15_amplitude_score(m15_amplitude_ratio),
        _session_score(in_session_overlap, in_single_session),
        _dxy_yields_score(dxy_change_pct, us10y_change_bp),
        _news_score(confirmed_major_news),
    ]
    total = min(10.0, sum(f.score for f in factors))

    if total <= 3:
        level, emoji = "faible", "🟢"
    elif total <= 6:
        level, emoji = "modere", "🟠"
    elif total <= 9:
        level, emoji = "eleve", "🔴"
    else:
        level, emoji = "exceptionnel", "🚨"

    return RiskAssessment(total_score=round(total, 1), level=level, emoji=emoji, factors=factors)


def is_volatility_normalized(atr14: float | None, atr_avg20: float | None, m15_amplitude_ratio: float | None) -> bool:
    """
    Regle de normalisation post-evenement (section 13/5) : ne jamais declarer un
    retour au calme sans confirmation par l'ATR et l'amplitude M15.
    """
    if atr14 is None or atr_avg20 is None or atr_avg20 == 0 or m15_amplitude_ratio is None:
        return False
    return (atr14 / atr_avg20) <= 1.2 and m15_amplitude_ratio <= 1.5
