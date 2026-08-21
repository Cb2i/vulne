# Agent XAUUSD.sc - Recherche, comparaison et architecture

Document de conception. Couvre les etapes 1 a 5 demandees : recherche des sources,
comparaison, architecture, mapping des sources et methodologie du Risk Engine.
Le format "rapport" (quotidien / hebdomadaire, 1.5 page max) est dans `examples/`.

## 1. Constat de depart

Aucun fournisseur unique ne couvre a la fois : prix spot XAU/USD temps reel, OHLC
multi-timeframe, indicateurs techniques, calendrier macro US et news qualifiees.
L'agent doit donc combiner plusieurs sources et appliquer une hierarchie stricte
en cas de desaccord (voir section 3).

Deux contraintes techniques verifiees pendant la recherche :

- **`XAUUSD.sc` est un symbole propre a PU Prime** (suffixe de compte/serveur). Il
  n'existe pas d'API publique ni de MCP exposant ce symbole precis avec son spread
  reel. Aucune source externe (Twelve Data, Alpha Vantage, etc.) ne peut donc
  garantir un prix identique au tick pres a celui affiche dans MT4. L'agent traite
  XAU/USD spot/futures comme **proxy de contexte** (tendance, niveaux, volatilite),
  jamais comme prix d'execution. Le prix d'execution reste MT4 uniquement.
- PU Prime ne publie pas d'API/MCP public pour les specifications de compte. Ces
  informations (horaires, spread, levier, rollover) doivent etre verifiees
  manuellement dans MT4 (Market Watch > clic droit sur XAUUSD.sc > Specification)
  et sur puprime.com, a une frequence hebdomadaire minimum, plus avant tout jour
  ferie US/UK connu.

## 2. Tableau comparatif des sources, API et MCP

| Nom | Donnees | Temps reel / differe | Cout | Limites | Fiabilite | MCP / API | Recommandation |
|---|---|---|---|---|---|---|---|
| **Federal Reserve (federalreserve.gov)** | Decisions FOMC, dot plot, discours Powell/gouverneurs | Temps reel (communiques officiels) | Gratuit | Pas d'API structuree, HTML/PDF a parser | Maximale (source primaire) | Aucun MCP officiel ; scraping/WebSearch cible | Obligatoire, niveau 1 |
| **BLS (bls.gov)** | CPI, Core CPI, NFP, chomage, JOLTS | Temps reel a l'heure de publication (08:30 ET) | Gratuit | Pas d'API temps reel publique simple, calendrier de publication fige a l'avance | Maximale | API BLS existante mais limitee ; utiliser surtout le calendrier officiel | Obligatoire, niveau 1 |
| **BEA (bea.gov)** | GDP, PCE, Core PCE | Temps reel a publication | Gratuit | API disponible mais peu documentee pour usage temps reel | Maximale | API officielle BEA | Obligatoire, niveau 1 |
| **U.S. Treasury / FRED (stlouisfed.org)** | US10Y (DGS10), US02Y (DGS2), courbe des taux | Quotidien (fin de journee, pas tick par tick) | Gratuit, cle API gratuite | Mise a jour une fois par jour ouvrable, pas intraday | Maximale (source primaire) | **API REST officielle FRED** (clé gratuite) | Obligatoire, niveau 1 pour les rendements |
| **CME Group** | Specs futures GC (COMEX), horaires Globex | Differe (temps reel payant) | Gratuit (specs) / payant (data temps reel, CME DataMine) | Donnees temps reel hors budget d'un usage individuel | Elevee | Pas de MCP ; API de donnees payante | Utiliser uniquement les specs publiques + horaires de marche, pas le flux prix |
| **World Gold Council (gold.org / Goldhub)** | Gold Demand Trends, reserves banques centrales | Trimestriel/mensuel, pas de prix | Gratuit | Pas d'API publique, rapports PDF/HTML | Elevee (source primaire sur la demande physique) | Aucun | Utiliser pour le narratif structurel (banques centrales, ETF), jamais pour un prix |
| **Twelve Data** | OHLC XAU/USD, M15/H1/H4/D, EMA/RSI/MACD/ATR precalcules, WebSocket | Temps reel selon plan (retard sur plan gratuit) | Gratuit : 8 req/min, 800/jour. Grow ~29 USD/mois. Pro ~99 USD/mois | Plan gratuit limite en frequence, WebSocket restreint | Bonne, usage large en production | **MCP officiel** (mcp.twelvedata.com) + API REST + WebSocket | **Recommande - source niveau 2 principale pour OHLC et indicateurs** |
| **Trading Economics** | Calendrier macro mondial, indicateurs historiques, previsions | Temps reel a publication | Standard ~149 USD/mois, Professional ~299 USD/mois (facturation annuelle). Essai limite (100 requetes) | Cout eleve pour un usage individuel | Bonne | **MCP officiel** (mcp.tradingeconomics.com) + serveur MCP communautaire (GitHub gavinHuang) + API REST | Recommande si budget disponible, sinon fallback ForexFactory + sources officielles |
| **ForexFactory (calendrier)** | Calendrier macro, consensus/precedent | Temps reel a publication | Gratuit | Non officiel : scraping, ToS a respecter, pas de garantie de stabilite | Moyenne (donnees generalement fiables mais non primaires) | MCP communautaire non officiel (kjpou1/forexfactory-mcp) | Fallback gratuit niveau 2/3, a croiser avec BLS/BEA/Fed pour tout chiffre cle |
| **Alpha Vantage** | Forex, commodites, 50+ indicateurs techniques | Gratuit : 25 requetes/jour, fin de journee. Payant : temps reel a partir de 49.99 USD/mois | Gratuit tres limite pour un usage quotidien H1/M15 | 25 req/jour insuffisant pour du intraday multi-timeframe | Bonne | **Support MCP officiel introduit en 2026** + API REST | Alternative/backup a Twelve Data, pas source principale (quota gratuit trop faible) |
| **GoldAPI.io** | Spot XAU/USD, XAG/USD, base LBMA/Forex | Temps reel | Gratuit : 500 requetes/mois. Payant au-dela | Petit fournisseur, pas de couverture multi-timeframe/indicateurs | Correcte pour un simple point de prix, a valider par recoupement | API REST uniquement | Backup ponctuel pour un prix spot, pas source unique |
| **Reuters / Bloomberg / FT / WSJ / CNBC** | Analyse, contexte, breaking news | Temps reel | Payant pour acces complet, extraits gratuits limites | Paywall partiel | Elevee (media niveau 3) | Aucun API/MCP simple, utiliser WebSearch cible | Niveau 3 : expliquer le "pourquoi", jamais la source d'un chiffre officiel |
| **Investing.com / TradingView / MarketWatch / FXStreet** | Cotations, analyses, calendrier | Temps reel/differe selon page | Gratuit avec limites | Fiabilite variable, articles d'opinion frequents | Moyenne | TradingView propose des API/webhooks payants, pas de MCP retenu | Niveau 4 : complement, jamais source unique d'un fait |
| **PU Prime (puprime.com / MT4)** | Specs XAUUSD.sc, horaires, spread, levier, rollover | Le seul flux reellement temps reel pour l'execution | Gratuit (compte client) | Pas d'API publique/MCP ; verification manuelle requise | Maximale pour l'execution, car c'est le broker reel | Aucun | Source unique de verite pour tout ce qui touche a l'execution reelle |

**Non retenus** : GC futures temps reel (CME DataMine, cout hors budget individuel),
Bloomberg Terminal/Refinitiv (cout entreprise), Financial Modeling Prep et
Intrinio (couverture actions US forte mais peu specialises XAU/USD/macro US,
redondants avec Twelve Data + Trading Economics pour ce cas d'usage).

## 3. Hierarchie des sources appliquee par l'agent

1. **Niveau 1 (verite officielle)** : Federal Reserve, BLS, BEA, U.S. Treasury/FRED,
   CME (specs), World Gold Council. Utilise pour : resultat exact d'une publication,
   rendements obligataires, decisions de taux.
2. **Niveau 2 (donnees de marche)** : PU Prime (execution reelle, verification
   manuelle), Twelve Data (OHLC + indicateurs, source principale automatisee),
   Trading Economics ou ForexFactory (calendrier, consensus/precedent).
3. **Niveau 3 (media financiers)** : Reuters, Bloomberg, FT, WSJ, CNBC. Utilise pour
   expliquer le contexte et le "pourquoi" d'un mouvement, jamais pour un chiffre
   officiel.
4. **Niveau 4 (complement)** : Investing.com, TradingView, MarketWatch, FXStreet.
   Utilise seulement pour completer, avec confirmation croisee obligatoire avant
   toute utilisation dans le Risk Score.

Regle de conflit : si deux sources divergent, l'agent (a) verifie date/heure de la
donnee, (b) verifie spot vs futures, (c) verifie le symbole exact, (d) privilegie le
niveau le plus bas (1 avant 2 avant 3 avant 4), (e) affiche explicitement l'ecart
et l'incertitude plutot que de choisir silencieusement une valeur.

## 4. Architecture technique

```
Market Data (Twelve Data MCP/API : OHLC M15/H1/H4/D, EMA/RSI/MACD/ATR)
        |
Economic Calendar (Trading Economics MCP si budget, sinon ForexFactory + verif BLS/BEA/Fed/Treasury)
        |
Official Sources (Federal Reserve, BLS, BEA, FRED : US10Y, US02Y, resultats macro)
        |
Financial News / WebSearch (Reuters, Bloomberg, FT, WSJ, CNBC -> le "pourquoi")
        |
PU Prime info (verification manuelle hebdomadaire : XAUUSD.sc, horaires, spread, levier)
        |
Technical Analysis Engine (EMA20/50/200, RSI14, MACD, ATR14, structure, niveaux)
        |
Risk Engine (score 0-10, timeline horaire, classification 🟢/🟠/🔴)
        |
Claude Agent (synthese, redaction, controle anti-hallucination)
        |
Rapport quotidien / hebdomadaire (Markdown, sans le caractere "-" long/em dash)
        |
Notification (fichier local, email ou webhook au choix de l'utilisateur)
```

**Frequence d'interrogation**
- Marche (Twelve Data) : rafraichi a chaque generation de rapport + cache 5 min pour
  eviter de depasser le quota gratuit (8 req/min).
- Calendrier macro : rafraichi une fois par rapport, cache 6h (le calendrier ne
  change pas souvent en cours de journee, sauf revision).
- Sources officielles (FRED, BLS, BEA) : rendements obligataires 1x/jour (donnee
  FRED elle-meme quotidienne) ; resultats macro verifies au moment de la
  publication puis fige.
- News : recherche ciblee au moment de la generation du rapport, fenetre de 24h
  (quotidien) ou 7 jours (hebdomadaire).
- Info PU Prime : verification manuelle hebdomadaire (script d'alerte si la
  derniere verification date de plus de 7 jours).

**Cache** : fichier local `cache/*.json` avec horodatage, invalide selon les TTL
ci-dessus. Objectif : rester dans les quotas gratuits et eviter les rapports
incoherents entre deux appels rapproches.

**Gestion des erreurs / fallback** : si Twelve Data echoue -> tentative Alpha
Vantage -> sinon la section technique concernee affiche "Donnee non disponible /
non verifiable" (jamais de valeur inventee). Meme logique pour le calendrier
(Trading Economics -> ForexFactory -> sources officielles seules).

**Validation croisee** : tout chiffre utilise dans le Risk Score (CPI, NFP, PCE,
decision Fed) doit correspondre a une source de niveau 1 avant d'etre marque
"confirme". Une source de niveau 3/4 seule reste marquee "non confirme".

**Fuseaux horaires** : toutes les heures sont calculees en UTC puis converties en
`America/Montreal` avec la librairie `zoneinfo` (regles DST officielles IANA), pas
de decalage fixe code en dur. Les sessions Asie/Londres/New York sont recalculees
a chaque rapport car les changements d'heure US/UK/Canada ne sont pas synchronises
(ex. mi-mars a debut avril, fin octobre a mi-novembre).

**Stockage historique** : SQLite local (`data/history.db`) pour les rapports
generes, les scores de risque quotidiens et les niveaux techniques, afin de
permettre la revue hebdomadaire ("performance de la semaine").

**Couts estimes (mensuel, config recommandee)**
- Twelve Data Grow (~29 USD) : necessaire des que le plan gratuit (8 req/min)
  devient limitant.
- Trading Economics : optionnel, ~149 USD/mois si le budget le permet, sinon
  ForexFactory + verification manuelle Fed/BLS/BEA (gratuit).
- FRED, Fed, BLS, BEA : gratuits.
- Config minimale viable : 0 USD/mois (Twelve Data gratuit + ForexFactory + FRED).
- Config confortable : ~30-180 USD/mois selon l'inclusion de Trading Economics.

## 5. Methodologie du Risk Score (0-10)

Score = somme ponderee de 6 facteurs, plafonnee a 10.

| Facteur | Poids max | Base de calcul |
|---|---|---|
| Importance/proximite de l'evenement macro | 4 | 4 si evenement majeur (CPI, NFP, PCE, FOMC) dans les 60 min ; 2 si dans les 2h ; 1 si dans la journee ; 0 sinon |
| Volatilite realisee (ATR14 H1 vs moyenne 20 jours) | 2 | 2 si ATR actuel > 1.5x moyenne ; 1 si > 1.2x ; 0 sinon |
| Amplitude M15 recente vs normale | 1 | 1 si les 3 dernieres bougies M15 depassent 2x l'amplitude moyenne |
| Session/chevauchement | 1 | 1 pendant le chevauchement Londres/New York, 0.5 en session Londres ou NY seule, 0 en session Asie calme |
| DXY / rendements US (mouvement recent) | 1 | 1 si DXY ou US10Y bouge de plus de 0.5% / 10 points de base sur la journee |
| Actualite/geopolitique majeure confirmee (niveau 1-2) | 1 | 1 si une nouvelle confirmee et non encore digeree par le marche |

Seuils d'affichage : 0-3 -> 🟢 faible, 4-6 -> 🟠 modere, 7-9 -> 🔴 eleve, 10 -> 🚨
exceptionnel. Le score et sa justification (quels facteurs ont contribue) sont
toujours affiches, jamais seulement le chiffre.

**Normalisation post-evenement** : le score ne redescend a 🟢 que lorsque l'ATR M15
redescend sous 1.2x sa moyenne ET qu'aucune bougie M15 recente ne depasse 1.5x
l'amplitude moyenne. Tant que ce n'est pas confirme, l'etat reste 🟠 "surveillance
post-evenement", jamais un retour automatique a 🟢 a heure fixe.

## 6. Limites connues de cette implementation

- Reseau sandbox de cette session : plusieurs domaines (kitco.com, fred.stlouisfed.org,
  bls.gov, tradingeconomics.com) sont bloques par le proxy de sortie utilise pour
  construire ce projet. Les exemples de rapports dans `examples/` sont donc des
  **gabarits illustratifs**, pas des rapports generes avec des donnees live. En
  production (environnement de l'utilisateur, hors sandbox), les collecteurs
  utilisent les API officielles (avec cle) plutot que le scraping HTML.
- `XAUUSD.sc` reste un symbole broker-only : le collecteur PU Prime est un stub a
  completer manuellement (voir `src/collectors/puprime.py`), aucune donnee n'est
  inventee a sa place.
