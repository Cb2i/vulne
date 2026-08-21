# Agent XAUUSD.sc - Veille et analyse de risque

Agent autonome de veille technique, macroeconomique et de risque pour
XAUUSD.sc (PU Prime, MT4, timeframe principal H1). Produit un rapport
quotidien (lundi-vendredi 06:30, dimanche 10:00, heure de Montreal) et un
rapport hebdomadaire (vendredi). Ne passe aucun ordre, ne pilote pas MT4, ne
modifie pas votre robot. Voir `ARCHITECTURE.md` pour la recherche, la
comparaison des sources/API/MCP et la methodologie complete.

## Ce que l'agent fait, et ne fait pas

Fait : collecte des donnees de marche et macro, calcule des indicateurs
techniques reels, calcule un Risk Score 0-10, construit une timeline horaire
du risque, redige un rapport structure, recommande quand suspendre/reprendre
le robot manuellement.

Ne fait pas : passer un ordre, se connecter a MT4, garantir un resultat,
inventer une donnee absente (affiche "Donnee non disponible / non
verifiable" a la place).

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # puis remplir les cles API
cp config/config.example.yaml config/config.yaml   # puis adapter si besoin
```

Cles utiles (toutes optionnelles individuellement, mais le rapport affichera
"Donnee non disponible" pour toute section dont la cle manque) :

- `TWELVE_DATA_API_KEY` : OHLC XAU/USD multi-timeframe (M15/H1/H4/D1). Plan
  gratuit suffisant pour demarrer (8 requetes/min, 800/jour).
- `FRED_API_KEY` : rendements US10Y/US02Y (source officielle, gratuite).
- `TRADING_ECONOMICS_API_KEY` : calendrier economique complet (payant, voir
  ARCHITECTURE.md pour le cout et l'alternative gratuite).
- `ALPHA_VANTAGE_API_KEY` : fallback daily si Twelve Data est indisponible.

## Utilisation

```bash
python main.py daily      # genere et sauvegarde le rapport quotidien maintenant
python main.py weekly     # genere et sauvegarde le rapport hebdomadaire maintenant
python main.py schedule   # demarre le planificateur (lun-ven 06:30, dim 10:00, ven weekly)
```

Les rapports sont sauvegardes dans `reports_out/` (Markdown) et, si
`NOTIFY_WEBHOOK_URL` est configure dans `.env`, envoyes egalement a ce
webhook. Les heures de planification sont en `America/Montreal` et gerent
automatiquement les changements EST/EDT (aucun decalage fixe code en dur, voir
`src/timezones.py`).

## Verification manuelle requise : PU Prime / XAUUSD.sc

PU Prime ne publie pas d'API ni de MCP public. Une fois par semaine minimum
(et avant tout jour ferie US/UK connu), verifiez manuellement dans MT4
(Market Watch > clic droit sur XAUUSD.sc > Specification) et sur puprime.com :
horaires de trading, spread typique, levier, rollover. Enregistrez le
resultat via `src/collectors/puprime.py::save_specs`. Ne confondez jamais
`XAUUSD.sc` avec `XAUUSD` ou `XAUUSD247`, qui sont des instruments differents
chez le meme broker.

## Structure du projet

```
ARCHITECTURE.md          recherche, comparaison des sources/API/MCP, architecture, Risk Engine
config/config.example.yaml   configuration (symbole, timezone, planification, sources)
src/timezones.py          conversions DST-safe (America/Montreal, New York, Londres, Tokyo)
src/collectors/           Twelve Data, FRED, calendrier macro, news, PU Prime
src/analysis/              EMA/RSI/MACD/ATR, niveaux (PDH/PDL, hebdo, S/R), sessions
src/risk/                  Risk Score 0-10 et timeline horaire du risque
src/reports/                gabarits Jinja2 + assemblage du contexte (aucune valeur inventee)
src/scheduler/              planification APScheduler (lun-ven 06:30, dim 10:00, ven weekly)
src/notify/                  sauvegarde fichier + webhook optionnel
src/storage.py               historique SQLite (pour le rapport hebdomadaire)
tests/                       tests unitaires (fuseaux horaires DST, indicateurs, Risk Engine)
examples/                    gabarits illustratifs de rapport quotidien et hebdomadaire
```

## Tests

```bash
python -m pytest tests/ -q
```

## Limites connues

Voir la section 6 de `ARCHITECTURE.md`. En resume : les exemples dans
`examples/` sont illustratifs (donnees fictives clairement marquees), le
reseau utilise pour construire ce projet bloquant l'acces direct a plusieurs
sources officielles (FRED, BLS, TradingEconomics). En production, avec des
cles API valides, les collecteurs retournent des donnees reelles ou
"Donnee non disponible / non verifiable" si une source echoue, jamais une
valeur inventee.
