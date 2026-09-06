# Schéma Excel — Job_Search_Dashboard.xlsx

Fichier stocké sur OneDrive/SharePoint (`/JobAgent/Reports/Job_Search_Dashboard.xlsx`), synchronisé
depuis Airtable par WF09 (après chaque candidature) et WF11 (rapport quotidien). Excel = miroir de
visualisation/backup ; Airtable reste la source de vérité opérationnelle.

## Feuille `Dashboard`

Vue synthèse "aujourd'hui", recalculée à chaque sync :

| Cellule / Colonne | Contenu |
|---|---|
| A1:B1 | `Date` / `=TODAY()` |
| A3:B15 | Offres trouvées, Nouvelles, Doublons, Analysées, Score ≥80, Score 70-79, Score 60-69, Rejetées, CV générés, Candidatures envoyées, Candidatures bloquées, Réponses reçues, Entretiens |
| D3:E10 | Mini-graphique (colonnes) : répartition par classification (PRIORITY/APPLY/MANUAL_REVIEW/REJECT) |
| Ces valeurs sont alimentées par une requête `Get rows` sur `DailyReports` (Airtable) filtrée sur la date du jour, écrites via le node Microsoft Excel "Update Row" |

## Feuille `Applications`

Copie miroir 1:1 de la table Airtable `Applications`. Colonnes identiques :

`application_id | job_id | company | title | application_date | cv_version | cover_letter |
overall_score | ats_score | application_method | status | last_update | response_type |
interview_date | notes`

Mise en forme conditionnelle :
- `status = INTERVIEW` → fond vert
- `status = BLOCKED_REQUIRES_MANUAL_ACTION` → fond orange
- `status = REJECTED` → fond gris
- `status = APPLIED` / `APPLICATION_CONFIRMED` → fond bleu clair

## Feuille `TopJobs`

Les offres `classification IN (PRIORITY, APPLY)` non encore traitées manuellement, triées par
`overall_score` décroissant :

`company | title | location | work_mode | salary_min | salary_max | overall_score | ats_score |
interview_probability_label | classification | url`

## Feuille `Interviews`

Sous-ensemble de `Applications` où `status IN (INTERVIEW, TECHNICAL_TEST)` :

`company | title | interview_date | response_type | notes | application_id`

## Feuille `Rejected`

Sous-ensemble `Jobs` où `classification = REJECT` :

`company | title | overall_score | rejection_reason | blocking_reasons | date_discovered`

## Feuille `ManualReview`

Sous-ensemble `Jobs` où `classification = MANUAL_REVIEW` (score 60-69) — jamais candidaté
automatiquement, présenté pour décision humaine :

`company | title | overall_score | technical_score | location_score | reason_summary | url`

## Feuille `Metrics`

Bloc de métriques agrégées (§40), recalculées sur une fenêtre glissante (7/30 jours) :

| Métrique | Formule / Source |
|---|---|
| Nombre d'offres découvertes | `COUNTA(Jobs.job_id)` sur la période |
| Nombre d'offres pertinentes | `COUNTIF(classification, "PRIORITY" OR "APPLY")` |
| Nombre de candidatures | `COUNTA(Applications.application_id)` |
| Taux de candidature | candidatures / offres pertinentes |
| Taux de réponse | réponses reçues / candidatures envoyées |
| Taux d'entretien | entretiens / candidatures envoyées |
| Taux de rejet | refus / candidatures envoyées |
| Score moyen | `AVERAGE(Jobs.overall_score)` |
| ATS moyen | `AVERAGE(Applications.ats_score)` |
| Sources générant le plus d'offres | Tableau croisé dynamique sur `Jobs.source` |
| Sources générant le plus d'entretiens | Croisement `Applications.status=INTERVIEW` ↔ `Jobs.source` |
| Technologies les plus demandées | Comptage sur `Jobs.technologies` (multi-valeur éclatée) |
| Titres les plus demandés | Comptage sur `Jobs.title` normalisé |
| Salaires moyens | `AVERAGE(Jobs.salary_min)`, `AVERAGE(Jobs.salary_max)` lorsque renseignés |

## Mécanique de synchronisation (nodes n8n)

1. `Microsoft Excel 365 → Append/Update Row` sur la feuille cible, avec `Sheet` = nom exact
   ci-dessus, `Table` = table Excel nommée identique (créer une **Table Excel** — pas juste une
   plage — pour permettre `Update Row` par clé, ex. `application_id` comme clé unique).
2. La feuille `Dashboard` et `Metrics` sont recalculées via formules natives Excel (pas de
   ré-écriture ligne par ligne), donc n8n n'écrit que dans `DailyReports`-like plage source ; les
   autres cellules se recalculent automatiquement à l'ouverture / via Excel Online.
