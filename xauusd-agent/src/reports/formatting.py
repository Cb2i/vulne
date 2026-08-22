"""Utilitaires de formatage communs aux rapports."""
from __future__ import annotations

NA = "Donnee non disponible / non verifiable"
FORBIDDEN_CHARS = ("—",)  # em dash

# Source niveau 4 (complement, verification manuelle) demandee par l'utilisateur.
# Liens fixes de reference, pas de scraping automatise : a recouper soi-meme,
# jamais utilises pour alimenter le Risk Score ou une valeur du rapport.
INVESTING_COM_REFS = [
    "Investing.com, niveau 4 - complement, verification manuelle : "
    "cours Or (https://www.investing.com/currencies/xau-usd) et "
    "calendrier economique (https://www.investing.com/economic-calendar/)",
]


def fmt_num(value: float | None, decimals: int = 2, suffix: str = "") -> str:
    if value is None:
        return NA
    return f"{value:.{decimals}f}{suffix}"


def fmt_list(values: list[float] | None) -> str:
    if not values:
        return NA
    return ", ".join(f"{v:.2f}" for v in values)


def strip_forbidden_chars(text: str) -> str:
    """Garantit l'absence du caractere em dash dans le rendu final (remplace par un tiret simple)."""
    for ch in FORBIDDEN_CHARS:
        text = text.replace(ch, "-")
    return text
