# Architecture — Plateforme de recherche d'emploi automatisée (Cybersécurité)

## 1. Vue d'ensemble

Système 100 % orchestré par **n8n**, composé de 12 workflows spécialisés qui s'appellent entre eux
(`Execute Workflow`), d'agents IA (Claude comme moteur principal, OpenAI comme second avis /
fallback), d'une base opérationnelle **Airtable**, d'un tableau de bord **Excel 365** (miroir), et
de notifications **Outlook (Microsoft 365)**.

Le système découvre des offres, les normalise, élimine les doublons, les fait analyser par Claude
(scoring multi-critères), fait contre-valider les offres à fort score par OpenAI, enrichit avec de
la recherche d'entreprise, adapte le CV maître (sans jamais inventer de faits), génère une lettre de
motivation si requise, répond aux questions standards de candidature, postule automatiquement quand
c'est techniquement et contractuellement permis, trace tout dans Airtable/Excel, surveille les
réponses par courriel, et envoie un rapport quotidien.

Aucune plateforme protégée par CAPTCHA, MFA, Cloudflare ou anti-bot n'est jamais contournée : le
système s'arrête proprement à `BLOCKED_REQUIRES_MANUAL_ACTION`.

## 2. Principes directeurs (non négociables)

1. **Zéro contournement de sécurité** — CAPTCHA, MFA, anti-bot, rate-limit, authentification :
   jamais outrepassés. En cas de blocage → `BLOCKED_REQUIRES_MANUAL_ACTION` + rapport.
2. **Zéro hallucination** — toute information utilisée dans un CV, une lettre ou une réponse de
   candidature doit être `SUPPORTED` (présente dans le CV maître / profil approuvé / offre /
   source publique fiable). Le statut `INFERRED` ne peut jamais devenir un fait présenté comme vrai.
   `UNKNOWN` → jamais deviné.
3. **Qualité > quota** — `MAX_APPLICATIONS_PER_DAY` est un plafond, pas un objectif.
4. **Traçabilité totale** — chaque décision IA (score, rejet, modification de CV, candidature)
   est journalisée avec `agent_name`, `model`, `timestamp`, `job_id`, `input_hash`, `score`,
   `decision`, `reason`.
5. **Modularité** — 12 workflows séparés, appelables indépendamment, plutôt qu'un monolithe.
6. **Sources autorisées uniquement** — API officielle > RSS > alertes courriel > endpoints publics
   > pages carrière publiques > moteurs de recherche > ATS publics. Jamais de scraping contre les
   conditions d'utilisation d'une plateforme.

## 3. Composants

| Composant | Rôle |
|---|---|
| **n8n** | Orchestrateur central, 12 workflows |
| **Claude (Anthropic API)** | Moteur IA principal : JOB_ANALYZER, COMPANY_RESEARCHER, CV_OPTIMIZER, APPLICATION_AGENT, EMAIL_RESPONSE_MONITOR |
| **OpenAI API** | Second avis / reviewer / extraction structurée / fallback si Claude indisponible |
| **Airtable** | Base opérationnelle principale (source de vérité) |
| **Excel 365 (OneDrive/SharePoint)** | Tableau de bord miroir, reporting, backup |
| **Microsoft Outlook (Graph)** | Envoi de rapports/alertes + surveillance des réponses de recrutement |
| **OneDrive / SharePoint** | Stockage des CV générés, lettres de motivation, rapports |
| **Google Drive** | Stockage du CV maître source (FR/EN) et base d'expérience approuvée (optionnel, miroir) |

## 4. Flux global (résumé — voir 02-workflow-diagram.md pour le détail)

```
Schedule Trigger (00:00 / 08:00 / 16:00 America/Toronto)
  → WF01 Job Discovery (multi-sources)
  → WF02 Job Normalizer (schéma JSON commun)
  → WF03 Deduplication (fingerprint SHA256 + Airtable lookup)
  → [NEW only] WF04 AI Job Analyzer (Claude) → OpenAI second avis si score ≥ 70
  → Decision (classification PRIORITY / APPLY / MANUAL_REVIEW / REJECT)
  → [score ≥ 70] WF05 Company Research (Claude)
  → WF06 CV Optimizer (Claude, score ATS)
  → WF07 CV Generator (PDF + lettre si requise, stockage OneDrive)
  → WF08 Application Agent (règle de candidature §30, sinon BLOCKED_REQUIRES_MANUAL_ACTION)
  → WF09 Application Tracker (Airtable + sync Excel)
  → Notification immédiate si score ≥ 90
  → WF10 Email Response Monitor (planifié séparément, ex: toutes les 30-60 min)
  → WF11 Daily Report (fin de journée, America/Toronto)
  → WF12 Error Handler (sous-workflow appelé par tous les autres en cas d'erreur)
```

## 5. Environnements

- **DEV** — instance n8n de développement, base Airtable "Job Search DEV", credentials sandbox.
- **TEST** — jeu de données de test (voir `07-test-plan.md`), sans candidature réelle envoyée
  (`APPLICATION_AUTOMATION_ALLOWED=false` global).
- **PROD** — instance n8n de production, `MAX_APPLICATIONS_PER_DAY` actif, notifications réelles.

Chaque workflow, prompt et schéma est versionné (voir `08-versioning.md`) via un champ `version`
explicite et un changelog, indépendamment des environnements.

## 6. Sécurité

- Toutes les clés API vivent dans **n8n Credentials**, jamais en dur dans un node.
- Les logs, rapports et Airtable ne stockent jamais : mots de passe, tokens, cookies, session IDs,
  ni réponses à des questions sensibles d'auto-identification (§28).
- Principe du moindre privilège : chaque credential n'a que les scopes nécessaires
  (ex. Outlook : Mail.Read, Mail.Send seulement — pas Mail.ReadWrite sur tous les dossiers).

## 7. Décomposition des agents IA

| Agent | Modèle principal | Rôle | Sortie |
|---|---|---|---|
| JOB_ANALYZER | Claude | Scoring multi-critères, classification, détection de critères bloquants | JSON structuré (voir schéma) |
| (Reviewer) | OpenAI | Second avis sur offres ≥70, détection d'hallucination/erreur de scoring | JSON structuré |
| COMPANY_RESEARCHER | Claude | Recherche publique sur l'entreprise (offres ≥70) | JSON structuré, `SUPPORTED/INFERRED/UNKNOWN` |
| CV_OPTIMIZER | Claude (+ OpenAI en contre-vérification ATS) | Adaptation du CV maître, calcul ATS_MATCH | JSON structuré + texte CV |
| APPLICATION_AGENT | Claude | Réponses aux questions standards, détection de questions sensibles/inconnues | JSON structuré |
| EMAIL_RESPONSE_MONITOR | Claude (OpenAI fallback) | Classification des courriels entrants, extraction d'entités | JSON structuré |

Voir `/prompts` pour les prompts système complets et `/schemas` pour les JSON Schemas de sortie
structurée de chaque agent.
