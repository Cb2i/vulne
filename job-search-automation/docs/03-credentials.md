# Liste exacte des credentials n8n nécessaires

Créer ces credentials dans **n8n → Credentials** avant d'importer les workflows. Les workflows
JSON référencent ces credentials par **nom** (placeholders explicites) ; il faudra les relier
dans n8n après import (n8n redemande la credential à l'import si l'ID ne correspond pas — c'est
normal et attendu).

| # | Nom du credential (à créer tel quel) | Type n8n | Utilisé par |
|---|---|---|---|
| 1 | `Anthropic account` | `anthropicApi` (ou Predefined Credential Type "Anthropic" sur HTTP Request) | WF04, WF05, WF06, WF08, WF10, WF12 |
| 2 | `OpenAI account` | `openAiApi` (ou Predefined Credential Type "OpenAi" sur HTTP Request) | WF04 (reviewer), WF06 (contre-vérif ATS), WF10 (fallback) |
| 3 | `Airtable Job Search PAT` | `airtableTokenApi` (Personal Access Token, scopes `data.records:read`, `data.records:write`, `schema.bases:read`) | tous les workflows (lecture/écriture Airtable) |
| 4 | `Microsoft Outlook OAuth2` | `microsoftOutlookOAuth2Api` | WF09 (notifications), WF10 (lecture boîte), WF11 (rapport quotidien), WF12 (alerte erreur critique) |
| 5 | `Microsoft OneDrive OAuth2` | `microsoftOneDriveOAuth2Api` | WF07 (stockage CV/lettres), WF06 (lecture CV maître) |
| 6 | `Microsoft Excel 365 OAuth2` | `microsoftExcelOAuth2Api` | WF09 (sync Excel), WF11 (sync Excel) |
| 7 | `Google Drive OAuth2` | `googleDriveOAuth2Api` | WF06 (lecture CV maître / base d'expérience si stockée sur Drive, optionnel) |
| 8 | `Indeed API` (si accès officiel obtenu) | Header Auth générique (`httpHeaderAuth`) | WF01 |
| 9 | `Guichet-Emplois Canada / Job Bank` (endpoints publics, généralement sans clé) | aucune credential requise (HTTP public) | WF01 |
| 10 | `LinkedIn Jobs (alertes courriel)` | aucune — traité via WF10/Outlook, pas d'API directe | WF01 (lecture d'alertes reçues par courriel), WF10 |
| 11 | `Jobillico RSS/API` (si disponible) | Header Auth générique si clé requise | WF01 |
| 12 | `Generic Career Pages HTTP` | aucune credential dédiée — HTTP Request public | WF01 |
| 13 | `n8n Internal Webhook Auth` (optionnel, si des sous-workflows exposent un Webhook) | Header Auth générique | WF12 (si alerting externe) |

## Notes importantes

- **Ne jamais** coller une clé API en dur dans un paramètre de node. Toujours passer par
  `Credentials` ou par des `n8n environment variables` référencées via `{{$env.VAR_NAME}}`
  uniquement pour des valeurs **non secrètes** (ex. seuils, timezone). Les vraies clés (Anthropic,
  OpenAI) doivent être dans un Credential n8n chiffré, jamais dans `$env`.
- Pour les sources sans API officielle (LinkedIn, Glassdoor, Jobboom si pas d'API), le mécanisme
  autorisé est la **réception d'alertes courriel** dans Outlook, lues par WF01 via le node
  Microsoft Outlook (Get Many Messages, dossier dédié `JobAlerts`), jamais le scraping direct du
  site.
- Chaque credential doit être scoping minimal :
  - Outlook : `Mail.Read`, `Mail.Send` uniquement.
  - OneDrive/SharePoint : accès limité au dossier `/JobAgent/` si possible (App Folder ou
    permissions déléguées scoping applicatif).
  - Airtable PAT : scoping limité à la base "Job Search" uniquement (pas accès à toutes les bases
    du compte).

## Placeholders utilisés dans les JSON n8n fournis

| Placeholder dans le JSON | À remplacer par |
|---|---|
| `REPLACE_WITH_ANTHROPIC_CREDENTIAL` | ID du credential `Anthropic account` créé dans votre instance |
| `REPLACE_WITH_OPENAI_CREDENTIAL` | ID du credential `OpenAI account` |
| `REPLACE_WITH_AIRTABLE_CREDENTIAL` | ID du credential `Airtable Job Search PAT` |
| `REPLACE_WITH_OUTLOOK_CREDENTIAL` | ID du credential `Microsoft Outlook OAuth2` |
| `REPLACE_WITH_ONEDRIVE_CREDENTIAL` | ID du credential `Microsoft OneDrive OAuth2` |
| `REPLACE_WITH_EXCEL_CREDENTIAL` | ID du credential `Microsoft Excel 365 OAuth2` |
| `REPLACE_WITH_GOOGLEDRIVE_CREDENTIAL` | ID du credential `Google Drive OAuth2` |
| `REPLACE_WITH_AIRTABLE_BASE_ID` | ID de votre base Airtable (`appXXXXXXXXXXXXXX`) |
