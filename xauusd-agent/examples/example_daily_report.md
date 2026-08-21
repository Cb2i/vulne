<!--
GABARIT ILLUSTRATIF, PAS UN RAPPORT REEL.
Le reseau utilise pour construire ce projet bloque l'acces direct a plusieurs
sources (FRED, BLS, Kitco, TradingEconomics), donc ce fichier ne peut pas etre
un rapport genere avec des donnees live verifiees. Il montre le format exact
que `main.py daily` produit une fois les cles API (Twelve Data, FRED,
Trading Economics) configurees. Les valeurs numeriques ci-dessous sont
fictives et clairement identifiees comme telles la ou c'est pertinent.
-->

# 🤖 XAUUSD.sc - MARKET STATUS

**Risk Score : 8/10 🔴**
**Tendance H1 : 🟢 Haussiere**
**Volatilite : 🔴 Elevee**
**Prochain evenement majeur : CPI US - 08:30 Montreal**
**Fenetre de risque : 08:15 a 09:00 - approche puis publication du CPI**

## RISQUE DU JOUR : 🔴 ELEVE (8/10)
🟢 06:00-08:15 Conditions normales
🔴 08:15-09:00 Publication CPI US (BLS, 08:30 heure Montreal)
🟠 09:00-09:45 Surveillance post-CPI, normalisation non confirmee
🟢 09:45-13:30 Conditions normalisees (a confirmer le jour meme par ATR/M15)
🔴 13:45-14:15 Discours de Jerome Powell (Fed, horaire a confirmer le jour meme)

## 1. Executive Summary
Contexte fictif d'illustration : structure H1 haussiere au-dessus des EMA20/50,
mais journee dominee par la publication du CPI US a 08:30 (heure Montreal). Le
Risk Score de 8/10 reflete surtout la proximite de cet evenement (4/4) et une
volatilite ATR14 deja au-dessus de sa moyenne 20 jours (2/2). Prudence
recommandee sur XAUUSD.sc autour de la publication.

## 2. Technical Analysis (Daily -> H4 -> H1 -> M15)
| Timeframe | Tendance | Structure | RSI14 | ATR14 |
|---|---|---|---|---|
| Daily | Haussiere | Range haut, proche des sommets recents | 58 | 21.40 |
| H4 | Haussiere | Higher highs / higher lows | 61 | 9.80 |
| H1 | Haussiere | Au-dessus EMA20/50/200 | 63 | 3.10 |
| M15 | Neutre | Consolidation avant CPI | 52 | 1.05 |

EMA20 : 2415.30 | EMA50 : 2398.10 | EMA200 : 2340.60
MACD (H1) : MACD 4.20 / Signal 3.10 / Hist 1.10

## 3. Key Levels
- Previous Day High : 2421.50
- Previous Day Low : 2402.10
- Weekly High : 2428.90
- Weekly Low : 2385.40
- Resistances : 2425.00, 2440.00
- Supports : 2400.00, 2385.00
- Zones psychologiques : 2400, 2450

## 4. Market Sessions (heure Montreal, DST prise en compte)
🌏 Asie : 20:00 - 05:00
🇬🇧 Londres : 03:00 - 11:30
🇺🇸 New York : 08:00 - 17:00
⚡ Chevauchement Londres/New York : 08:00 - 11:30

## 5. Economic Calendar
| Heure | Evenement | Importance | Consensus | Precedent | Resultat |
|---|---|---|---|---|---|
| 08:30 | CPI US (m/m) | Haute | 0.3% | 0.2% | en attente |
| 08:30 | Core CPI US (m/m) | Haute | 0.3% | 0.3% | en attente |
| 13:45 | Discours Jerome Powell | Haute | - | - | en attente |

## 6. DXY & Treasury Yields
- DXY : donnee non disponible dans cet exemple (a completer par le collecteur live)
- US10Y : exemple 4.28% (source : FRED, date fictive)
- US02Y : exemple 4.05% (source : FRED, date fictive)
- Lecture contextuelle : un CPI plus faible que prevu ferait typiquement baisser
  DXY et les rendements, contexte generalement favorable a l'or, mais la
  reaction reelle dependra de la composante coeur et du ton de Powell l'apres-midi.

## 7. Important News
- CPI attendu en leger ralentissement selon le consensus des economistes
  (Source : Reuters, exemple, 21 aout 2026) - Impact potentiel : eleve sur XAU/USD si surprise -
  Confiance : non confirme (a recouper avec le resultat BLS reel)

## 8. Risk Timeline
| Heure Montreal | Niveau | Raison |
|---|---|---|
| 06:00-08:15 | 🟢 | Conditions normales |
| 08:15-09:00 | 🔴 | Publication CPI US |
| 09:00-09:45 | 🟠 | Surveillance post-CPI, normalisation non confirmee |
| 09:45-13:30 | 🟢 | Conditions normalisees (sous reserve de confirmation ATR/M15) |
| 13:45-14:15 | 🔴 | Discours Powell |

## 9. Points to Monitor
- Ne pas declarer la fin du risque a 09:00 sans confirmation ATR/amplitude M15.
- Verifier la reaction du marche a la composante Core CPI, souvent plus suivie que le CPI headline.
- Confirmer les specifications XAUUSD.sc dans MT4 (spread, horaires) avant la publication.

**Recommandation robot EA (a valider par vous-meme, pas un ordre) :**
- Arret suggere : au plus tard 08:15, avant la publication du CPI.
- Reprise suggeree : pas avant 09:00, et seulement si l'ATR H1 et l'amplitude
  M15 confirment un retour sous 1.2x/1.5x leur moyenne recente. Sinon,
  rester en pause jusqu'a normalisation confirmee, y compris apres le
  discours de Powell a 13:45.

## 10. Sources
- Twelve Data (OHLC/indicateurs) - exemple
- BLS (CPI, calendrier officiel) - exemple
- Federal Reserve (discours Powell) - exemple
- FRED (US10Y, US02Y) - exemple
- Reuters (contexte) - exemple

---
Ce rapport est une veille de marche et une analyse de risque. Il ne constitue pas
un conseil en investissement, ne garantit aucun rendement et ne declenche aucun
ordre. Decision finale : vous seul.
