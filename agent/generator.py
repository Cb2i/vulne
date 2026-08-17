"""Génération de variantes typosquattées d'un nom de domaine.

Techniques classiques (inspirées de dnstwist) : omission, répétition,
transposition, substitution clavier (qwerty), homoglyphes, tirets,
variation de TLD, et combinaisons avec des mots-clés de marque
(ex: "exemple-securite.com").
"""

from __future__ import annotations

QWERTY_ADJACENCY = {
    "a": "qwsz", "b": "vghn", "c": "xdfv", "d": "erfcxs", "e": "wsdr",
    "f": "rtgdcv", "g": "tyhbfv", "h": "yujnbg", "i": "ujko", "j": "uikmnh",
    "k": "iolmj", "l": "kop", "m": "njk", "n": "bhjm", "o": "iklp",
    "p": "ol", "q": "wa", "r": "edft", "s": "awedxz", "t": "rfgy",
    "u": "yhji", "v": "cfgb", "w": "qase", "x": "zsdc", "y": "tghu",
    "z": "asx",
}

HOMOGLYPHS = {
    "o": ["0"], "l": ["1", "i"], "i": ["1", "l"], "e": ["3"],
    "a": ["4"], "s": ["5"], "b": ["8"], "g": ["9"],
}

ALT_TLDS = [
    "com", "net", "org", "info", "biz", "co", "io", "xyz", "top",
    "site", "online", "club", "cc", "app", "shop", "store",
]

BRAND_PATTERNS = ["{k}-{n}", "{n}-{k}", "{k}{n}", "{n}{k}"]
DEFAULT_KEYWORDS = ["secure", "support", "login", "account", "verify", "mail"]


def _split_domain(domain: str) -> tuple[str, str]:
    parts = domain.rsplit(".", 1)
    if len(parts) != 2:
        raise ValueError(f"Domaine invalide: {domain}")
    return parts[0], parts[1]


def _omissions(name: str) -> set[str]:
    return {name[:i] + name[i + 1:] for i in range(len(name))}


def _repetitions(name: str) -> set[str]:
    return {name[:i] + ch + name[i:] for i, ch in enumerate(name)}


def _transpositions(name: str) -> set[str]:
    out = set()
    for i in range(len(name) - 1):
        chars = list(name)
        chars[i], chars[i + 1] = chars[i + 1], chars[i]
        out.add("".join(chars))
    return out


def _adjacent_subs(name: str) -> set[str]:
    out = set()
    for i, ch in enumerate(name):
        for sub in QWERTY_ADJACENCY.get(ch, ""):
            out.add(name[:i] + sub + name[i + 1:])
    return out


def _homoglyphs(name: str) -> set[str]:
    out = set()
    for i, ch in enumerate(name):
        for sub in HOMOGLYPHS.get(ch, []):
            out.add(name[:i] + sub + name[i + 1:])
    return out


def _hyphenation(name: str) -> set[str]:
    return {name[:i] + "-" + name[i:] for i in range(1, len(name))}


def generate_candidates(
    domain: str,
    brand_keywords: list[str] | None = None,
    max_candidates: int = 400,
) -> list[str]:
    """Retourne une liste dédupliquée de domaines candidats à vérifier."""
    domain = domain.lower().strip()
    name, tld = _split_domain(domain)
    keywords = list(dict.fromkeys((brand_keywords or []) + DEFAULT_KEYWORDS))

    variants: set[str] = set()
    variants |= _omissions(name)
    variants |= _repetitions(name)
    variants |= _transpositions(name)
    variants |= _adjacent_subs(name)
    variants |= _homoglyphs(name)
    variants |= _hyphenation(name)
    variants.discard(name)
    variants = {v for v in variants if v and not v.startswith("-") and not v.endswith("-")}

    candidates = {f"{v}.{tld}" for v in variants}

    for alt_tld in ALT_TLDS:
        if alt_tld != tld:
            candidates.add(f"{name}.{alt_tld}")

    for kw in keywords:
        for pattern in BRAND_PATTERNS:
            candidates.add(f"{pattern.format(k=kw, n=name)}.{tld}")

    candidates.discard(domain)
    ordered = sorted(candidates)
    return ordered[:max_candidates]
