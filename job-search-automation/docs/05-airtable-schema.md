# Schéma Airtable — Base "Job Search"

Créer une base Airtable nommée `Job Search` (ou `Job Search DEV/TEST/PROD`) avec les 8 tables
suivantes. Les types de champ Airtable sont indiqués entre parenthèses.

## Table `Jobs`

| Champ | Type | Notes |
|---|---|---|
| `job_id` | Single line text (Primary) | UUID généré à la normalisation |
| `fingerprint` | Single line text | SHA256 (§16), indexé pour dédup |
| `source` | Single select | Indeed, LinkedIn, Glassdoor, Jobillico, Jobboom, GuichetEmplois, QuebecEmploi, CareerPage, Workday, Greenhouse, Lever, SmartRecruiters, Workable, iCIMS, Taleo, SuccessFactors, Other |
| `source_job_id` | Single line text | ID natif de la source |
| `company` | Single line text | |
| `title` | Single line text | |
| `url` | URL | Page de l'offre |
| `application_url` | URL | Lien de candidature |
| `location` | Single line text | Ville brute |
| `country` | Single select | Canada, USA, Other |
| `province` | Single line text | |
| `work_mode` | Single select | onsite, hybrid, remote |
| `employment_type` | Single select | full_time, part_time_evening, contract, internship, other |
| `salary_min` | Number | |
| `salary_max` | Number | |
| `salary_currency` | Single select | CAD, USD, Other |
| `salary_bonus` | Long text | Prime/bonus si extrait |
| `salary_benefits` | Long text | Avantages, pension, actions, vacances |
| `date_posted` | Date | |
| `date_discovered` | Date | |
| `description` | Long text | |
| `requirements` | Long text (JSON array stringifié) | |
| `technologies` | Multiple select | Sentinel, Defender XDR, Defender for Endpoint, Defender for Cloud, Defender Vulnerability Mgmt, Entra ID, Intune, Azure, Purview, KQL, Logic Apps, SOAR, Tenable, CrowdStrike, Palo Alto, AWS Security, QRadar, SIEM, EDR, XDR, IAM, PAM, CSPM, Other |
| `certifications` | Multiple select | |
| `languages` | Multiple select | French, English |
| `security_clearance` | Single select | none, eligible_to_obtain, required_held, unknown |
| `easy_apply` | Checkbox | |
| `overall_score` | Number | 0-100 |
| `technical_score` | Number | |
| `experience_score` | Number | |
| `ats_score` | Number | |
| `location_score` | Number | |
| `language_score` | Number | |
| `seniority_score` | Number | |
| `salary_score` | Number | |
| `interview_probability_score` | Number | 0-100 |
| `interview_probability_label` | Single select | LOW, MEDIUM, HIGH, VERY_HIGH |
| `classification` | Single select | PRIORITY, APPLY, MANUAL_REVIEW, REJECT |
| `status` | Single select | NEW, DUPLICATE, ALREADY_APPLIED, UPDATED_JOB, ANALYZED |
| `blocking_reasons` | Multiple select | location_incompatible, onsite_required_outside_quebec, canada_not_accepted, clearance_required, not_cybersecurity, student_internship, salary_below_threshold, already_applied, expired |
| `rejection_reason` | Long text | |
| `second_opinion_used` | Checkbox | |
| `second_opinion_divergence` | Number | |
| `applications` | Link to `Applications` | |
| `companies` | Link to `Companies` | |
| `created_at` | Created time | |
| `updated_at` | Last modified time | |

## Table `Applications`

| Champ | Type | Notes |
|---|---|---|
| `application_id` | Single line text (Primary) | UUID |
| `job_id` | Link to `Jobs` | |
| `company` | Lookup (via job_id) | |
| `title` | Lookup (via job_id) | |
| `application_date` | Date | |
| `cv_version` | Link to `CVVersions` | |
| `cover_letter` | Attachment / URL | |
| `overall_score` | Number | |
| `ats_score` | Number | |
| `application_method` | Single select | auto_easy_apply, auto_form, manual_required, email |
| `status` | Single select | DISCOVERED, ANALYZING, QUALIFIED, CV_GENERATED, READY_TO_APPLY, APPLIED, APPLICATION_CONFIRMED, REQUIRES_MANUAL_REVIEW, BLOCKED_REQUIRES_MANUAL_ACTION, INTERVIEW, TECHNICAL_TEST, REJECTED, OFFER, CLOSED |
| `blocking_reason` | Long text | Renseigné si `BLOCKED_REQUIRES_MANUAL_ACTION` |
| `last_update` | Last modified time | |
| `response_type` | Single select | APPLICATION_CONFIRMATION, RECRUITER_MESSAGE, INTERVIEW_REQUEST, TECHNICAL_TEST, REJECTION, JOB_OFFER, REQUEST_FOR_INFORMATION, UNKNOWN, none |
| `interview_date` | Date | |
| `notes` | Long text | |

## Table `Companies`

| Champ | Type | Notes |
|---|---|---|
| `company_id` | Single line text (Primary) | |
| `name` | Single line text | |
| `industry` | Single line text | |
| `size_estimate` | Single select | 1-50, 51-200, 201-1000, 1000-5000, 5000+, unknown |
| `technologies_mentioned` | Long text | |
| `microsoft_environment` | Single select | SUPPORTED, INFERRED, UNKNOWN |
| `cloud_environment` | Long text | |
| `security_posture_notes` | Long text | |
| `recent_projects` | Long text | |
| `research_confidence` | Single select | SUPPORTED, INFERRED, UNKNOWN |
| `research_date` | Date | |
| `jobs` | Link to `Jobs` | |

## Table `CVVersions`

| Champ | Type | Notes |
|---|---|---|
| `cv_version_id` | Single line text (Primary) | |
| `job_id` | Link to `Jobs` | |
| `language` | Single select | FR, EN |
| `file_name` | Single line text | `CV_Aboubacar_[Entreprise]_[Poste]_[YYYYMMDD].pdf` |
| `onedrive_path` | URL | |
| `base_ats_score` | Number | Score du CV original avant optimisation |
| `optimized_ats_score` | Number | |
| `iterations` | Number | Nombre de boucles d'optimisation |
| `changes_summary` | Long text | Résumé des modifications (réorg., mots-clés, etc.) |
| `created_at` | Created time | |

## Table `ApplicationAnswers`

> **Ne jamais** y stocker de réponses à des questions sensibles d'auto-identification (§28).

| Champ | Type | Notes |
|---|---|---|
| `answer_id` | Single line text (Primary) | |
| `application_id` | Link to `Applications` | |
| `question_text` | Long text | |
| `question_category` | Single select | technical, experience, availability, language, work_authorization, sensitive_excluded |
| `answer_value` | Long text | `UNKNOWN` si non connu avec certitude |
| `confidence` | Single select | SUPPORTED, INFERRED, UNKNOWN |
| `source_reference` | Single line text | Référence au profil/CV justifiant la réponse |

## Table `AgentRuns`

| Champ | Type | Notes |
|---|---|---|
| `run_id` | Single line text (Primary) | |
| `agent_name` | Single select | JOB_ANALYZER, OPENAI_REVIEWER, COMPANY_RESEARCHER, CV_OPTIMIZER, APPLICATION_AGENT, EMAIL_RESPONSE_MONITOR |
| `model` | Single line text | ex. `claude-sonnet-5`, `gpt-4.1` |
| `job_id` | Link to `Jobs` | |
| `input_hash` | Single line text | |
| `score` | Number | |
| `decision` | Single line text | |
| `reason` | Long text | Explication concise et auditable (§45) |
| `timestamp` | Created time | |

## Table `Errors`

| Champ | Type | Notes |
|---|---|---|
| `error_id` | Single line text (Primary) | |
| `workflow` | Single line text | |
| `node` | Single line text | |
| `timestamp` | Created time | |
| `input_id` | Single line text | job_id/application_id concerné, si applicable |
| `error_code` | Single line text | |
| `error_message` | Long text | |
| `retry_count` | Number | |
| `resolved` | Checkbox | |

## Table `DailyReports`

| Champ | Type | Notes |
|---|---|---|
| `report_date` | Date (Primary) | |
| `jobs_found` | Number | |
| `jobs_new` | Number | |
| `jobs_duplicate` | Number | |
| `jobs_analyzed` | Number | |
| `jobs_score_80plus` | Number | |
| `jobs_score_70_79` | Number | |
| `jobs_score_60_69` | Number | |
| `jobs_rejected` | Number | |
| `cvs_generated` | Number | |
| `applications_sent` | Number | |
| `applications_blocked` | Number | |
| `responses_received` | Number | |
| `interviews` | Number | |
| `rejections` | Number | |
| `technical_tests` | Number | |
| `avg_score` | Number | |
| `avg_ats_score` | Number | |
| `top_sources` | Long text | |
| `top_technologies` | Long text | |
| `top_titles` | Long text | |
| `report_html` | Long text | Corps HTML envoyé par courriel |

## Vues recommandées

- `Jobs` → vue `To Review` (`classification = MANUAL_REVIEW`), vue `Priority Today`
  (`classification = PRIORITY AND date_discovered = TODAY()`).
- `Applications` → vue `Blocked` (`status = BLOCKED_REQUIRES_MANUAL_ACTION`), vue `Active
  Pipeline` (`status IN (APPLIED, INTERVIEW, TECHNICAL_TEST)`).
- `Errors` → vue `Unresolved` (`resolved = false`).
