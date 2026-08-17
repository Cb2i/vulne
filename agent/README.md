# Agent de surveillance anti-typosquatting

Détecte automatiquement les domaines "typosquattés" (fautes de frappe,
homoglyphes, TLD alternatifs, combinaisons avec des mots-clés de marque)
ressemblant à votre domaine, vérifie s'ils sont actifs (DNS, WHOIS,
certificat TLS), fait trier les nouvelles détections par Claude (optionnel),
puis envoie une alerte par email et/ou webhook Slack/Teams.

## Pourquoi cet agent plutôt que la suite Microsoft Defender ?

La suite Microsoft (Defender for Office 365, MDTI, EASM) protège vos
utilisateurs contre le phishing entrant et cartographie *vos* actifs
exposés, mais n'offre pas de veille automatisée sur les nouveaux domaines
enregistrés qui imitent votre marque. Cet agent comble ce manque et peut
tourner en complément de votre stack Microsoft.

## Architecture

```
agent/
  generator.py   génère les variantes typosquattées du domaine
  checks.py      vérifie DNS / WHOIS / Certificate Transparency (crt.sh)
  triage.py      score le risque (Claude si ANTHROPIC_API_KEY, sinon règles)
  alerts.py      envoie l'alerte (email SMTP, webhook Slack/Teams)
  state.py       mémorise les domaines déjà vus pour n'alerter que sur le neuf
  main.py        orchestrateur / point d'entrée CLI
```

Deux modes d'exécution planifiée sont fournis :

- **GitHub Actions** (`.github/workflows/typosquat-scan.yml`) — cron
  quotidien, aucune infra à gérer.
- **Azure Function** (`azure_function/`) — timer trigger, pour rester dans
  l'écosystème Microsoft/Azure et bénéficier d'Application Insights,
  Key Vault, etc.

Les deux réutilisent le même code métier dans `agent/`.

## Configuration

Toutes les options sont pilotées par variables d'environnement (voir
`agent/config.py`) :

| Variable | Description |
|---|---|
| `TARGET_DOMAIN` | Domaine à surveiller (ex: `cb2i.fr`). **Placeholder par défaut : `example.com`.** |
| `BRAND_KEYWORDS` | Mots-clés de marque séparés par des virgules, combinés au domaine (ex: `cb2i,monentreprise`) |
| `ANTHROPIC_API_KEY` | Optionnel. Active le triage IA des détections via Claude. Sans elle, un scoring par règles est utilisé. |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` | Configuration SMTP pour l'alerte email |
| `ALERT_EMAIL_FROM`, `ALERT_EMAIL_TO` | Expéditeur / destinataires (`ALERT_EMAIL_TO` accepte plusieurs adresses séparées par des virgules) |
| `SLACK_WEBHOOK_URL` | Webhook entrant Slack |
| `TEAMS_WEBHOOK_URL` | Webhook entrant Teams (connecteur "Incoming Webhook") |
| `AGENT_STATE_PATH` | Chemin du fichier d'état (défaut `agent/state.json`) |
| `AGENT_FINDINGS_PATH` | Chemin du rapport JSON complet (défaut `agent/findings.json`) |

## Utilisation locale

```bash
pip install -r agent/requirements.txt
export TARGET_DOMAIN=cb2i.fr
export BRAND_KEYWORDS=cb2i
python -m agent.main --dry-run   # génère et vérifie sans envoyer d'alerte ni écrire d'état
python -m agent.main             # exécution réelle
```

## Déploiement GitHub Actions

1. Dans les paramètres du dépôt : **Settings → Secrets and variables →
   Actions**.
2. Ajouter les *variables* `TARGET_DOMAIN` et `BRAND_KEYWORDS`.
3. Ajouter les *secrets* : `ANTHROPIC_API_KEY` (optionnel), `SMTP_*`,
   `ALERT_EMAIL_FROM`, `ALERT_EMAIL_TO`, `SLACK_WEBHOOK_URL`,
   `TEAMS_WEBHOOK_URL` (selon les canaux souhaités).
4. Le workflow tourne chaque jour à 06h00 UTC, et peut être lancé
   manuellement via "Run workflow".

## Déploiement Azure Function

```bash
cd azure_function
cp local.settings.json.example local.settings.json   # puis renseigner les valeurs, ne pas committer
func start   # test local (nécessite Azure Functions Core Tools)
```

Pour le déploiement, la Function App doit avoir accès au dossier `agent/`
à côté d'elle. Deux options :

- **Monorepo direct** : déployer la racine du dépôt en gardant
  `azure_function/` et `agent/` comme dossiers frères (le `sys.path.insert`
  dans `function_app.py` s'en charge).
- **Package autonome** : copier `agent/` dans `azure_function/agent/` avant
  `func azure functionapp publish` si votre pipeline CI/CD ne package que
  le dossier de la function.

Renseignez les mêmes variables d'environnement que ci-dessus dans
**Application settings** de la Function App (idéalement via Key Vault
references pour `ANTHROPIC_API_KEY` et `SMTP_PASSWORD`).

## Limites connues / améliorations futures

- Le triage IA analyse les signaux techniques (DNS/WHOIS/certificat) mais
  ne charge pas les pages détectées — ajouter une capture d'écran +
  comparaison visuelle (ex: via Playwright) affinerait encore le scoring.
- La détection Certificate Transparency vérifie chaque candidat
  individuellement ; un flux temps réel type CertStream permettrait une
  détection plus rapide mais nécessite un processus persistant plutôt
  qu'un cron.
- Les résultats (`agent/findings.json`) sont prêts à être branchés sur un
  futur panneau dédié dans `vuln_manager.html`.
