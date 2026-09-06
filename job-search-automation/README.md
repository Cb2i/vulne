# Plateforme automatisée de recherche d'emploi — Cybersécurité (n8n)

Système complet et importable dans n8n pour automatiser la recherche d'emploi et la candidature
en cybersécurité : découverte multi-sources, scoring IA (Claude + second avis OpenAI), recherche
d'entreprise, adaptation de CV sans hallucination, candidature automatique encadrée, suivi des
réponses courriel, et rapport quotidien.

## Structure du dépôt

```
job-search-automation/
├── README.md                         ← ce fichier (guide de déploiement)
├── docs/
│   ├── 01-architecture.md            ← Livrable 1 : architecture complète
│   ├── 02-workflow-diagram.md        ← Livrable 2 : diagramme des workflows (Mermaid)
│   ├── 03-credentials.md             ← Livrable 3 : credentials n8n exacts
│   ├── 04-environment-variables.md   ← Livrable 4 : variables d'environnement
│   ├── 05-airtable-schema.md         ← Livrable 5 : schéma Airtable
│   ├── 06-excel-schema.md            ← Livrable 6 : schéma Excel
│   ├── 07-test-plan.md               ← Livrable : plan de test (§52)
│   └── 08-versioning.md              ← Livrable : versioning DEV/TEST/PROD
├── prompts/
│   ├── 01-job-analyzer.md            ← Livrable 7
│   ├── 02-company-researcher.md      ← Livrable 8
│   ├── 03-cv-optimizer.md            ← Livrable 9
│   ├── 04-application-agent.md       ← Livrable 10
│   └── 05-email-response-monitor.md  ← Livrable 11
├── schemas/                          ← Livrable 12 : JSON Schema de sortie de chaque agent
│   ├── job_analyzer.schema.json
│   ├── company_researcher.schema.json
│   ├── cv_optimizer.schema.json
│   ├── application_agent.schema.json
│   └── email_response_monitor.schema.json
└── workflows/                        ← Livrables 13+ : JSON n8n réellement importables
    ├── WF01_JOB_DISCOVERY.json
    ├── WF02_JOB_NORMALIZER.json
    ├── WF03_DEDUPLICATION.json
    ├── WF04_AI_JOB_ANALYZER.json
    ├── WF05_COMPANY_RESEARCH.json
    ├── WF06_CV_OPTIMIZER.json
    ├── WF07_CV_GENERATOR.json
    ├── WF08_APPLICATION_AGENT.json
    ├── WF09_APPLICATION_TRACKER.json
    ├── WF10_EMAIL_RESPONSE_MONITOR.json
    ├── WF11_DAILY_REPORT.json
    └── WF12_ERROR_HANDLER.json
```

## Déploiement — ordre exact à suivre

1. **Créer la base Airtable** selon `docs/05-airtable-schema.md` (8 tables). Noter le Base ID.
2. **Créer le fichier Excel** `Job_Search_Dashboard.xlsx` selon `docs/06-excel-schema.md`, le
   déposer sur OneDrive/SharePoint dans `/JobAgent/Reports/`.
3. **Créer les credentials n8n** listés dans `docs/03-credentials.md`.
4. **Définir les variables n8n** listées dans `docs/04-environment-variables.md` (Settings →
   Variables), avec `AIRTABLE_BASE_ID` = Base ID de l'étape 1.
5. **Importer les 12 workflows dans cet ordre : WF12 → WF11 → WF10 → WF09 → WF08 → WF07 → WF06 →
   WF05 → WF04 → WF03 → WF02 → WF01** (ordre inverse des dépendances, pour pouvoir renseigner
   chaque `workflowId` "REPLACE_WITH_WFxx_WORKFLOW_ID" au fur et à mesure que les workflows cibles
   existent déjà).
6. Pour chaque workflow importé :
   - Relier les credentials (n8n vous le demandera — voir la table de correspondance dans
     `docs/03-credentials.md`).
   - Dans les nodes `Execute Workflow`, remplacer le placeholder `REPLACE_WITH_WFxx_WORKFLOW_ID`
     par l'ID réel du workflow cible (déjà importé grâce à l'ordre ci-dessus).
   - Dans `Settings du workflow → Error Workflow`, sélectionner **WF12_ERROR_HANDLER**.
7. Activer WF01 (Schedule 00:00/08:00/16:00), WF10 (Schedule 30 min) et WF11 (Schedule 22:00).
   Les autres (WF02-WF09, WF12) restent en mode "appelé par sous-workflow" — les activer aussi
   (`active: true`) pour qu'ils acceptent les appels `Execute Workflow`.
8. Régler le fuseau horaire de l'instance n8n sur `America/Toronto` (variable d'environnement
   n8n `GENERIC_TIMEZONE=America/Toronto` et `TZ=America/Toronto`).
9. Exécuter le plan de test (`docs/07-test-plan.md`) en environnement **TEST**
   (`APPLICATION_AUTOMATION_ALLOWED=false`) avant tout passage en PROD.

## Points nécessitant une adaptation à votre instance (signalés dans chaque workflow)

- **Référence exacte des fichiers OneDrive** (CV maître, dossier de sortie) dans WF06/WF07 —
  les modes de resource locator (`id`/`path`/`url`) varient selon la version du node Microsoft
  OneDrive installée.
- **Conversion HTML → PDF** (WF07) via l'endpoint de conversion de format Microsoft Graph
  (`?format=pdf`) — fonctionne pour les fichiers `.docx`/`.html` supportés par Graph ; testez avec
  un exemple réel et ajustez si votre tenant a des restrictions.
- **Soumission automatique de candidature** (WF08, node `Submit_Application_Auto`) — livré comme
  gabarit générique. À n'activer/adapter que pour une intégration officiellement autorisée
  (API partenaire ATS). Par défaut, la quasi-totalité des candidatures passeront par
  `BLOCKED_REQUIRES_MANUAL_ACTION`, ce qui est le comportement sûr et attendu tant qu'aucune
  intégration n'est confirmée.
- **Sources de découverte** (WF01) — les URLs RSS de Jobillico/Job Bank et les slugs
  Greenhouse/Lever (`GREENHOUSE_SLUGS_CSV`, `LEVER_SLUGS_CSV`) sont des points de configuration à
  compléter avec vos propres cibles autorisées.
- **Résumé du CV maître dans les prompts** (`master_cv_summary` dans WF04, texte extrait réel
  dans WF06) — remplacer les placeholders par l'extraction réelle de votre CV.

## Garde-fous non négociables déjà intégrés

- Aucun node ne contourne CAPTCHA/MFA/anti-bot — `APPLICATION_AGENT` détecte et bloque
  (`BLOCKED_REQUIRES_MANUAL_ACTION`), jamais de tentative de contournement.
- `CV_OPTIMIZER` ne peut produire que des faits présents dans le CV maître (contrôlé par le
  prompt système, voir `prompts/03-cv-optimizer.md`).
- La règle de candidature automatique (§30) est implémentée intégralement et littéralement dans
  `WF08_APPLICATION_AGENT.json` (node `Evaluate_Application_Rule`).
- `MAX_APPLICATIONS_PER_DAY` est vérifié par comptage réel des candidatures du jour dans Airtable,
  pas par un compteur en mémoire.
- Chaque décision IA est journalisée dans la table `AgentRuns` avec `reason` auditable.
