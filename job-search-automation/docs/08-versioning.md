# Versioning — DEV / TEST / PROD

## Environnements

| Environnement | Base Airtable | `APPLICATION_AUTOMATION_ALLOWED` | Fichier Excel | Usage |
|---|---|---|---|---|
| DEV | `Job Search DEV` | `false` | `Job_Search_Dashboard_DEV.xlsx` | Développement de nouveaux nodes/prompts |
| TEST | `Job Search TEST` | `false` | `Job_Search_Dashboard_TEST.xlsx` | Exécution du plan de test (`07-test-plan.md`) |
| PROD | `Job Search PROD` | `true` | `Job_Search_Dashboard.xlsx` | Utilisation réelle, candidatures automatiques actives |

Chaque environnement est une **instance n8n distincte** (ou un espace de travail n8n distinct avec
ses propres Variables et Credentials) — jamais un simple changement de variable sur la même
instance qui pourrait faire fuiter une exécution TEST vers PROD.

## Versionnage des artefacts

Chaque fichier de `/prompts`, `/schemas` et `/workflows` porte (ou doit porter, une fois importé
dans n8n) un identifiant de version :

- **Prompts** (`/prompts/*.md`) : ligne `version: X.Y.Z` en tête de fichier. Incrémenter :
  - `PATCH` (Z) : clarification de formulation sans changement de comportement.
  - `MINOR` (Y) : ajout d'une règle ou d'un champ de sortie, rétrocompatible.
  - `MAJOR` (X) : changement de format de sortie ou de logique de décision.
- **Schémas** (`/schemas/*.json`) : champ `"version"` dans le JSON, même convention.
- **Workflows n8n** : utiliser le versioning natif de n8n (chaque sauvegarde crée une révision
  consultable dans l'historique du workflow) + renommer explicitement le workflow lors d'un
  changement majeur de logique, ex. `WF04_AI_JOB_ANALYZER_v2`, le temps de valider en TEST avant
  de remplacer la version PROD.
- **Règles de scoring** (pondérations §18) : versionnées via les variables d'environnement
  (`WEIGHT_*`) — conserver un changelog manuel dans ce fichier à chaque changement de pondération
  en PROD :

| Date | Changement | Auteur | Raison |
|---|---|---|---|
| _(à compléter)_ | Pondérations initiales (30/20/15/10/10/10/5) | — | Valeurs de référence du cahier des charges initial |

## Promotion DEV → TEST → PROD

1. Développer/modifier un workflow ou un prompt en DEV.
2. Exporter le JSON du workflow (`...` → Download) et le comparer au fichier versionné dans ce
   dépôt (`/job-search-automation/workflows/`) — committer le diff avec un message explicite.
3. Importer en TEST, exécuter le plan de test complet (`07-test-plan.md`).
4. Si tous les cas passent, importer en PROD, garder `active=false` le temps d'une première
   exécution manuelle de vérification, puis activer.
5. Ne jamais activer un workflow PROD dont le Error Workflow (WF12) n'est pas configuré.
