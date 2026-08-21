"""
Actualites financieres (niveau 3/4). Ce module ne fait PAS d'appel HTTP direct :
il definit le contrat de donnees que l'agent Claude remplit via son propre outil
de recherche web (WebSearch/WebFetch cote agent), avec obligation de renseigner
source + date + heure pour chaque item. Voir README pour le flux d'integration.
"""
from __future__ import annotations

from dataclasses import dataclass

ALLOWED_TIER3 = ("Reuters", "Bloomberg", "Financial Times", "Wall Street Journal", "CNBC")
ALLOWED_TIER4 = ("Investing.com", "TradingView", "MarketWatch", "FXStreet")


@dataclass
class NewsItem:
    summary: str
    source: str
    published_at: str  # ISO 8601, obligatoire
    potential_impact: str  # ex: "haussier pour l'or", "baissier", "incertain"
    confidence: str  # "confirme" (niveau 1/2 recoupe) ou "non confirme"

    def __post_init__(self) -> None:
        if not self.source or not self.published_at:
            raise ValueError("source et published_at sont obligatoires (anti-hallucination)")


def filter_relevant(items: list[NewsItem], max_items: int = 5) -> list[NewsItem]:
    """Garde les items les plus recents et rejette le sensationnalisme non source."""
    ranked = sorted(items, key=lambda i: i.published_at, reverse=True)
    return ranked[:max_items]
