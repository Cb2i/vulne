# Variables d'environnement

À définir dans **n8n → Settings → Variables** (n8n Variables, disponibles via `{{$vars.NOM}}`)
ou en variables d'environnement du conteneur n8n (`{{$env.NOM}}`) selon votre déploiement. Aucune
de ces variables n'est un secret — les vraies clés API restent dans les Credentials (voir
`03-credentials.md`).

## Configuration générale

| Variable | Exemple / défaut | Description |
|---|---|---|
| `TIMEZONE` | `America/Toronto` | Fuseau horaire utilisé par tous les Schedule Trigger et l'horodatage des rapports |
| `ENVIRONMENT` | `DEV` \| `TEST` \| `PROD` | Environnement actif, utilisé pour préfixer logs et choisir la base Airtable |
| `AIRTABLE_BASE_ID` | `appXXXXXXXXXXXXXX` | ID de la base Airtable "Job Search" |

## Candidature automatique

| Variable | Exemple / défaut | Description |
|---|---|---|
| `MAX_APPLICATIONS_PER_DAY` | `5` | Plafond quotidien de candidatures automatiques (§29) |
| `APPLICATION_AUTOMATION_ALLOWED` | `true` | Interrupteur global — `false` en TEST pour ne jamais soumettre réellement |
| `MIN_OVERALL_SCORE_TO_APPLY` | `70` | Seuil minimal `overall_score` pour candidature automatique |
| `MIN_ATS_SCORE_TO_APPLY` | `80` | Seuil minimal `ats_score` pour candidature automatique |
| `PRIORITY_SCORE_THRESHOLD` | `80` | Seuil de classification `PRIORITY` |
| `MANUAL_REVIEW_MIN_SCORE` | `60` | Seuil bas de la tranche `MANUAL_REVIEW` (60-69) |
| `HIGH_ALERT_SCORE_THRESHOLD` | `90` | Seuil déclenchant la notification immédiate (§38) |
| `SALARY_TARGET_MIN` | `` (à déterminer) | Seuil salarial configurable — ne filtre jamais si vide |

## Scoring (pondérations, §18 — modifiables sans toucher aux prompts)

| Variable | Défaut | Description |
|---|---|---|
| `WEIGHT_TECHNICAL` | `30` | Poids compétences techniques |
| `WEIGHT_EXPERIENCE` | `20` | Poids expérience |
| `WEIGHT_TECHNOLOGIES` | `15` | Poids technologies |
| `WEIGHT_SENIORITY` | `10` | Poids séniorité |
| `WEIGHT_LOCATION` | `10` | Poids localisation |
| `WEIGHT_ATS` | `10` | Poids ATS / mots-clés |
| `WEIGHT_LANGUAGE` | `5` | Poids langues |
| `SECOND_OPINION_SCORE_THRESHOLD` | `70` | Seuil déclenchant le second avis OpenAI (§21) |
| `SECOND_OPINION_DIVERGENCE_THRESHOLD` | `10` | Écart de points déclenchant une 2e analyse Claude (§21) |

## Localisation (§6)

| Variable | Défaut | Description |
|---|---|---|
| `HOME_PROVINCE` | `Quebec` | Province de résidence du candidat |
| `HOME_CITY` | `Quebec City` | Ville de résidence |
| `ACCEPT_US_REMOTE_REQUIRES_CANADA_MENTION` | `true` | N'accepte une offre US remote que si "Canada" est explicitement mentionné comme éligible |
| `MAX_OCCASIONAL_TRIPS_PER_YEAR` | `4` | Nombre max de déplacements occasionnels acceptés |
| `MONTREAL_MAX_ONSITE_DAYS_PER_MONTH` | `1` | Présence occasionnelle acceptée à Montréal (~1x/mois) |

## Runtime / CV

| Variable | Défaut | Description |
|---|---|---|
| `CV_FR_MASTER_PATH` | `/JobAgent/MasterCV/CV_Aboubacar_Master_FR.docx` | Chemin OneDrive du CV maître FR |
| `CV_EN_MASTER_PATH` | `/JobAgent/MasterCV/CV_Aboubacar_Master_EN.docx` | Chemin OneDrive du CV maître EN |
| `ONEDRIVE_ROOT_FOLDER` | `/JobAgent` | Racine de l'arborescence (§25) |
| `ATS_MATCH_TARGET` | `80` | Objectif minimal ATS_MATCH après optimisation (§24) |
| `CV_OPTIMIZER_MAX_ITERATIONS` | `3` | Nombre max de boucles de réécriture avant d'accepter le meilleur score atteint |

## Email

| Variable | Défaut | Description |
|---|---|---|
| `OUTLOOK_MAILBOX` | `REPLACE_WITH_YOUR_OUTLOOK_EMAIL` | Boîte Microsoft 365 / Outlook surveillée par WF10 (doit correspondre au compte lié au credential OAuth2 Outlook) |
| `OUTLOOK_JOB_ALERTS_FOLDER` | `JobAlerts` | Dossier Outlook recevant les alertes LinkedIn/Indeed/etc. utilisé par WF01 |
| `EMAIL_MONITOR_LOOKBACK_MINUTES` | `90` | Fenêtre de lecture des nouveaux courriels à chaque exécution WF10 |
| `DAILY_REPORT_SEND_TIME` | `22:00` | Heure d'envoi du rapport quotidien (America/Toronto) |
| `NOTIFICATION_RECIPIENT` | `REPLACE_WITH_YOUR_NOTIFICATION_EMAIL` | Destinataire des alertes et du rapport quotidien |

## Résilience (§43)

| Variable | Défaut | Description |
|---|---|---|
| `API_TIMEOUT_RETRY_COUNT` | `3` | Nombre d'essais sur timeout API |
| `RATE_LIMIT_BACKOFF_BASE_MS` | `2000` | Base du backoff exponentiel sur 429 |
| `RATE_LIMIT_BACKOFF_MAX_RETRIES` | `4` | Nombre max de retries sur 429 |
| `ERROR_NOTIFICATION_THRESHOLD` | `5` | Nombre d'erreurs consécutives avant alerte critique par courriel |

> Toutes ces valeurs sont lues via `{{$vars.NOM}}` dans les Code nodes et les expressions des
> workflows fournis, afin de pouvoir les ajuster sans modifier la logique.
