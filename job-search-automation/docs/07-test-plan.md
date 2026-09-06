# Plan de test (§52)

Environnement recommandé : **TEST** (`APPLICATION_AUTOMATION_ALLOWED=false`, base Airtable
`Job Search TEST`), pour valider toute la chaîne sans jamais soumettre de vraie candidature.

Pour chaque cas : injecter manuellement un item dans WF02 (ou directement dans WF04 pour cibler le
scoring) via **n8n → Execute Workflow with test data** (bouton "Test workflow" avec un JSON
d'entrée pinné sur le node trigger), puis vérifier le résultat attendu dans Airtable.

| # | Cas de test | Entrée simulée (points clés) | Résultat attendu |
|---|---|---|---|
| 1 | Offre parfaite | Senior Security Analyst, Québec, Sentinel+Defender+Azure+KQL, permanent temps plein, salaire publié | `overall_score >= 90`, `classification=PRIORITY`, notification immédiate envoyée (WF09) |
| 2 | Offre moyenne | Intermédiaire, 2 technologies prioritaires sur 5, Montréal hybride | `overall_score` ~65-75, selon technicité → `APPLY` ou `MANUAL_REVIEW` |
| 3 | Mauvaise offre | Poste développeur logiciel sans lien cybersécurité | `classification=REJECT`, `blocking_reasons` contient `not_cybersecurity` |
| 4 | Poste Toronto hybride | Ontario, hybride 3j/semaine | `location_match` faible, `blocking_reasons` contient `onsite_required_outside_quebec` sauf si remote dominant → vérifier classification cohérente |
| 5 | Poste Québec hybride | Ville de Québec, hybride | `location_match` élevé (règle Ville de Québec accepte tout), pas de blocage lié à la localisation |
| 6 | Poste Canada remote | Toronto, 100% remote, pas de présence requise | `location_match` élevé (reste du Canada = remote uniquement, ici respecté) |
| 7 | Poste USA remote USA seulement | "Remote (US only)", aucune mention Canada | `blocking_reasons` contient `canada_not_accepted`, `classification=REJECT` |
| 8 | Poste USA remote Canada accepté | "Remote - Canada-based candidates welcome" | Pas de `canada_not_accepted`, scoring normal |
| 9 | Offre dupliquée | Même entreprise/titre/localisation/URL qu'une offre déjà en base | WF03 → `dedup_status=DUPLICATE`, aucun nouvel enregistrement Jobs, pas de re-candidature |
| 10 | Annonce republiée (même poste) | Même fingerprint, description légèrement modifiée, déjà `APPLIED` en base | WF03 → `ALREADY_APPLIED` (car statut existant = APPLIED), aucune candidature envoyée |
| 11 | Cote de sécurité obligatoire | "Active Secret clearance required" (non détenue) | `blocking_reasons` contient `clearance_required`, `classification=REJECT` |
| 12 | Cote "eligible to obtain" | "Must be eligible to obtain Reliability Status" | Pas de `clearance_required`, scoring normal |
| 13 | CV score faible | Offre technique éloignée du profil (ex. développement mobile) | WF06 : `optimized_ats_score` reste bas malgré itérations, `gaps_not_coverable` non vide, aucune fabrication de compétence |
| 14 | Question inconnue obligatoire | Question de formulaire sans réponse dans le profil approuvé, marquée obligatoire | WF08 : `has_unknown_mandatory_question=true` → `can_auto_apply=false` → `BLOCKED_REQUIRES_MANUAL_ACTION` |
| 15 | CAPTCHA détecté | Contexte simulant une détection CAPTCHA/anti-bot sur le formulaire | APPLICATION_AGENT retourne `blocked=true` → `BLOCKED_REQUIRES_MANUAL_ACTION`, jamais de tentative de contournement |
| 16 | Claude indisponible | Simuler une erreur HTTP 500/timeout sur `Call_Claude_Email_Monitor` (WF10) | Sortie d'erreur du node déclenche `Call_OpenAI_Fallback`, classification produite quand même |
| 17 | OpenAI indisponible | Simuler une erreur sur `Call_OpenAI_Reviewer` (WF04) | Le node échoue selon la politique de retry (3 essais) ; en TEST, vérifier que le job continue avec l'analyse Claude seule si vous ajoutez une branche de fallback équivalente (voir note ci-dessous) |
| 18 | Airtable indisponible | Simuler une erreur 500 sur un node Airtable | WF12 reçoit l'erreur via Error Workflow, log tenté (peut échouer aussi si Airtable est down — surveiller manuellement dans ce cas extrême) |
| 19 | Confirmation de candidature | Courriel type "Your application has been received" | WF10 → `classification=APPLICATION_CONFIRMATION`, statut Airtable mis à `APPLICATION_CONFIRMED` |
| 20 | Rejet | Courriel type "We have decided to move forward with other candidates" | WF10 → `classification=REJECTION`, statut mis à `REJECTED` |
| 21 | Invitation entretien | Courriel proposant une date d'entretien | WF10 → `classification=INTERVIEW_REQUEST`, statut mis à `INTERVIEW`, `proposed_date` extraite |

## Note sur le cas 17 (fallback OpenAI → Claude)

Le prompt WF04 tel que livré effectue Claude → (si score ≥70) OpenAI reviewer → (si divergence
>10) Claude 2e analyse. Si vous voulez un fallback symétrique (OpenAI indisponible ne bloque pas
le pipeline), configurez le node `Call_OpenAI_Reviewer` avec `retryOnFail`/`onError:
continueErrorOutput` comme fait dans WF10, et routez la sortie d'erreur directement vers
`Consolidate_Without_Second_Analysis` (le second avis est alors simplement absent, ce qui est
acceptable : ce n'est qu'une contre-vérification, pas un blocant).

## Validation de non-régression après toute modification de prompt/scoring

1. Rejouer les 21 cas ci-dessus.
2. Vérifier qu'aucune candidature `APPLIED` n'a été créée en environnement TEST.
3. Vérifier la table `Errors` : aucune erreur non expliquée par le scénario testé.
4. Vérifier `AgentRuns` : chaque décision porte un `reason` non vide et cohérent.
