# Sentinel 2027 — Epic : Optimisation de la visibilité et de la traçabilité

**Statut :** En avancement (mode advance)
**Produit concerné :** VulnContext — Gestionnaire de vulnérabilités contextuel (`vuln_manager.html`)
**Horizon :** Roadmap 2027

## Contexte

VulnContext calcule aujourd'hui un score de risque contextualisé (CVSS → score ajusté) et génère un billet de vulnérabilité via IA, mais l'outil reste **100 % client-side et sans mémoire** :

- Aucune persistance : `state.vulns` vit uniquement en mémoire JS et disparaît au rafraîchissement de la page.
- Aucune trace de qui a créé/modifié/clôturé un billet, ni quand.
- Aucun historique des ajustements de score dans le temps (pas de comparaison avant/après sur plusieurs semaines).
- Aucun tableau de bord agrégé au-delà des 4 compteurs KPI instantanés (`cnt-crit/high/med/low`).
- Aucun statut de cycle de vie du billet (nouveau, en cours, en attente de patch, résolu, risque accepté) — un billet est soit "non généré", soit "généré", point final.
- Aucune intégration réelle avec Microsoft Sentinel / MDVM : les requêtes KQL sont générées en texte mais jamais exécutées ni reliées à un incident.
- Aucun contrôle d'accès : n'importe qui ouvrant le fichier HTML a un accès complet en lecture/écriture, sans notion d'auteur.

Cet epic vise à transformer VulnContext d'un simulateur de scoring en **outil traçable et auditable**, condition nécessaire à son usage en contexte opérationnel (SOC, conformité Loi 25/PIPEDA, reporting RSSI).

## Objectifs mesurables (Definition of Done de l'epic)

- 100 % des vulnérabilités et de leurs modifications sont persistées et attribuables à un auteur + horodatage.
- Le RSSI peut reconstituer, pour n'importe quel billet, l'historique complet des décisions (score, statut, contrôles) sans accès aux logs bruts.
- Un tableau de bord affiche les tendances (ouverts/résolus, respect SLA) sur au moins 90 jours glissants.
- Aucune perte de données possible lors d'un rafraîchissement de navigateur ou d'un changement de poste.

---

## Feature 1 — Persistance des vulnérabilités et des billets

**Objectif :** éliminer la perte de données au rafraîchissement ; rendre les vulnérabilités consultables dans le temps.

| # | Tâche | Priorité | Estimation |
|---|-------|----------|------------|
| 1.1 | Concevoir le modèle de données persistant (vulnérabilité, contexte asset, contrôles, billet, historique) | P0 | 3 pts |
| 1.2 | Mettre en place le backend de stockage (API + base de données) remplaçant `state.vulns` en mémoire | P0 | 8 pts |
| 1.3 | Migrer le front-end pour charger/sauvegarder via l'API au lieu du state JS local | P0 | 5 pts |
| 1.4 | Ajouter horodatage `créé le` / `modifié le` sur chaque enregistrement | P1 | 2 pts |
| 1.5 | Gérer la reprise de session (rechargement de la liste au démarrage, pas de perte si onglet fermé) | P1 | 3 pts |

## Feature 2 — Journal d'audit des décisions (audit trail)

**Objectif :** rendre chaque changement de score, de statut ou de contrôle compensatoire traçable et non-répudiable.

| # | Tâche | Priorité | Estimation |
|---|-------|----------|------------|
| 2.1 | Définir le schéma d'événement d'audit (acteur, action, valeur avant/après, horodatage, billet concerné) | P0 | 2 pts |
| 2.2 | Journaliser chaque ajustement de score (`adjustedScore`) avec la justification déjà calculée | P0 | 3 pts |
| 2.3 | Journaliser chaque bascule de contrôle compensatoire (EDR, MFA, segmentation, WAF, backup) | P1 | 2 pts |
| 2.4 | Journaliser les régénérations de billet AI (`btn-regen`) et les exports (`btn-export`) | P1 | 2 pts |
| 2.5 | Rendre le journal immuable (append-only) et consultable par billet | P0 | 5 pts |
| 2.6 | Exposer une vue "historique" dans le panneau billet, listant les événements dans l'ordre chronologique | P2 | 5 pts |

## Feature 3 — Cycle de vie et statuts des billets

**Objectif :** dépasser le binaire "généré / non généré" pour refléter l'état réel de remédiation.

| # | Tâche | Priorité | Estimation |
|---|-------|----------|------------|
| 3.1 | Introduire un champ statut : Nouveau → En cours → En attente de patch → Résolu → Risque accepté | P0 | 3 pts |
| 3.2 | Contraindre les transitions de statut valides (machine à états) et les journaliser (lien avec Feature 2) | P1 | 3 pts |
| 3.3 | Afficher le statut comme badge dans la liste de priorité (`vuln-card`) et le filtrer | P1 | 3 pts |
| 3.4 | Alerter visuellement les billets proches ou en dépassement de leur SLA (`priority.sla`) | P1 | 3 pts |
| 3.5 | Exiger une justification texte au passage en statut "Risque accepté" (traçabilité de l'acceptation) | P2 | 2 pts |

## Feature 4 — Tableau de bord de visibilité globale

**Objectif :** donner une vue agrégée et temporelle au-delà des 4 compteurs instantanés actuels.

| # | Tâche | Priorité | Estimation |
|---|-------|----------|------------|
| 4.1 | Étendre les KPI actuels (crit/haute/moyenne/faible) avec une tendance sur 30/90 jours | P1 | 5 pts |
| 4.2 | Ajouter un indicateur de conformité SLA (% de billets résolus dans les délais par priorité) | P0 | 5 pts |
| 4.3 | Ajouter des filtres/segments (par asset, type d'exposition, équipe responsable) | P2 | 3 pts |
| 4.4 | Ajouter une vue "delta CVSS → score ajusté" agrégée pour valider la pertinence du moteur de scoring | P2 | 3 pts |
| 4.5 | Export du tableau de bord en rapport exécutif (PDF/PPT) pour le RSSI | P2 | 5 pts |

## Feature 5 — Intégration Microsoft Sentinel / MDVM

**Objectif :** relier les requêtes KQL générées à une exécution réelle et boucler la boucle de détection ↔ remédiation.

| # | Tâche | Priorité | Estimation |
|---|-------|----------|------------|
| 5.1 | Connecter VulnContext à l'API Microsoft Sentinel (authentification, workspace) | P1 | 8 pts |
| 5.2 | Permettre l'exécution des requêtes KQL générées directement depuis le billet, avec affichage des résultats | P1 | 5 pts |
| 5.3 | Créer automatiquement un incident Sentinel lié au billet (référence croisée bidirectionnelle) | P2 | 5 pts |
| 5.4 | Synchroniser le statut MDVM (patch appliqué / CVE toujours présente) avec le statut du billet (Feature 3) | P2 | 5 pts |

## Feature 6 — Contrôle d'accès et traçabilité multi-analyste

**Objectif :** attribuer chaque action à une personne identifiée, prérequis de tout audit de conformité.

| # | Tâche | Priorité | Estimation |
|---|-------|----------|------------|
| 6.1 | Ajouter l'authentification des utilisateurs (SSO / Azure AD) | P0 | 8 pts |
| 6.2 | Définir les rôles (Analyste, RSSI, Lecture seule) et les permissions associées | P1 | 5 pts |
| 6.3 | Attribuer un auteur à chaque création/modification de vulnérabilité et de billet | P0 | 3 pts |
| 6.4 | Vue "activité par analyste" pour le RSSI (charge de travail, délais de traitement) | P2 | 5 pts |

---

## Séquencement proposé

1. **Sprint 1-2 :** Feature 1 (persistance) — bloquant pour tout le reste.
2. **Sprint 3 :** Feature 6.1/6.3 (auth minimale + attribution auteur) + Feature 2 (audit trail) — les deux sont interdépendantes.
3. **Sprint 4 :** Feature 3 (statuts et cycle de vie).
4. **Sprint 5 :** Feature 4 (tableau de bord).
5. **Sprint 6+ :** Feature 5 (intégration Sentinel/MDVM) et reste de Feature 6.

## Risques

- La Feature 5 (intégration Sentinel) dépend de la disponibilité d'un tenant Azure/Sentinel de test — à valider avec l'équipe infra avant sprint 6.
- Le passage d'un outil 100 % client-side à une architecture avec backend (Feature 1) est un changement structurant : à traiter comme un choix d'architecture explicite, pas une simple tâche technique.
