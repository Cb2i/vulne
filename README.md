# VulnAssist

Application web interne de gestion des vulnérabilités : import des exports Tenable, calcul du
score contextuel **CAA**, application des délais de remédiation **SLE**, attribution automatique
des équipes propriétaires, gestion des exceptions, décommissionnement d'actifs, comparaison de
scans, regroupement des remédiations, tableaux de bord KPI et exports Excel.

L'application est un **monolithe** volontairement simple : un backend FastAPI et un frontend React
compilé, déployés comme un seul processus sur un serveur interne (Windows ou Linux). **Aucune
dépendance à Docker, Kubernetes ou à un service cloud** n'est requise.

## Sommaire

- [Architecture](#architecture)
- [Prérequis](#prérequis)
- [Installation rapide (scripts automatisés)](#installation-rapide-scripts-automatisés)
- [Installation manuelle détaillée](#installation-manuelle-détaillée)
- [Configuration](#configuration)
- [Lancement](#lancement)
- [Utilisation](#utilisation)
- [Développement](#développement)
- [Tests](#tests)
- [Migration vers PostgreSQL](#migration-vers-postgresql)
- [Sauvegarde](#sauvegarde)
- [Rôles et permissions](#rôles-et-permissions)
- [Structure du projet](#structure-du-projet)

## Architecture

```
                     UTILISATEUR
                         │
                         │ Navigateur (réseau interne)
                         ▼
               ┌───────────────────┐
               │    VulnAssist     │
               │   (1 processus)   │
               └─────────┬─────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
        React / TypeScript       FastAPI (/api)
      (servi en statique par        │
         FastAPI en prod)           │
                 ┌────────────────────┼─────────────────────┐
                 │                    │                     │
                 ▼                    ▼                     ▼
           Moteur Excel        Moteur métier          Export Engine
        (pandas / openpyxl)    (app/rules/*)          (openpyxl)
                               │
                  ┌────────────┼────────────┐
                  │            │            │
                  ▼            ▼            ▼
                 CAA          SLE        Ownership
                  │            │            │
                  └────────────┼────────────┘
                               ▼
                       Remediation Engine
                               │
                               ▼
                        SQLite / PostgreSQL
```

- **Backend** : Python, FastAPI, SQLAlchemy 2.0, Alembic, Pandas/OpenPyXL, Pydantic v2,
  Argon2id pour le hachage des mots de passe, JWT pour l'authentification.
- **Frontend** : React 18, TypeScript, Vite, React Router, Recharts — interface sombre inspirée
  des consoles de cybersécurité modernes, optimisée pour un usage desktop.
- **Base de données** : SQLite par défaut (aucun serveur additionnel requis) ; les modèles
  SQLAlchemy sont écrits pour être portables vers PostgreSQL sans changement de code applicatif.
- **Déploiement** : un seul processus `uvicorn` sert à la fois l'API REST (`/api/*`) et les
  fichiers statiques compilés du frontend (`frontend/dist`).

## Prérequis

| Composant | Version minimale | Notes |
|---|---|---|
| Python | 3.11 | https://www.python.org/downloads/ |
| Node.js | 18 LTS | https://nodejs.org/ (requis uniquement pour compiler le frontend) |
| SQLite | — | inclus avec Python, aucune installation requise |
| PostgreSQL | 14+ | **optionnel**, uniquement si vous choisissez de migrer plus tard |

Aucun accès Internet n'est requis en production : l'application ne dépend d'aucune police, script
ou service tiers chargé depuis un CDN, et aucune intégration cloud (Azure, Entra ID, Teams, Power
BI) n'est utilisée.

## Installation rapide (scripts automatisés)

### Windows Server / Windows 10-11

```powershell
cd C:\path\to\vulnassist
.\scripts\install.ps1
.\scripts\start.ps1
```

> Si l'exécution de scripts PowerShell est bloquée, lancez d'abord (en administrateur, une seule
> fois) :
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### Linux

```bash
cd /opt/vulnassist
./scripts/install.sh
./scripts/start.sh
```

Ouvrez ensuite `http://localhost:8000` (ou `http://<nom-du-serveur>:8000` depuis un autre poste du
réseau interne).

Identifiants par défaut créés au premier lancement (à changer immédiatement) :
- **E-mail** : `admin@vulnassist.internal`
- **Mot de passe** : `ChangeMe123!`

## Installation manuelle détaillée

Si vous préférez ne pas utiliser les scripts, ou pour comprendre chaque étape :

### 1. Installer Python

Téléchargez et installez Python 3.11+ depuis https://www.python.org/downloads/. Sur Windows,
cochez **"Add python.exe to PATH"** pendant l'installation.

### 2. Créer l'environnement virtuel

```bash
cd backend
python -m venv .venv
```

Activation :
```powershell
# Windows
.venv\Scripts\activate
```
```bash
# Linux / macOS
source .venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Créer la base de données

```bash
copy .env.example .env      # Windows : "cp .env.example .env" sous Linux
alembic upgrade head        # crée le schéma (SQLite par défaut, dans ../data/vulnassist.db)
python -m app.seed          # crée l'admin par défaut, les règles CAA/SLE et les équipes de base
```

### 5. Compiler le frontend

```bash
cd ../frontend
npm install
npm run build
```

Le résultat est généré dans `frontend/dist/`. En production, FastAPI sert directement ce dossier
— aucun serveur web supplémentaire (nginx, IIS, Apache) n'est nécessaire.

### 6. Configuration

Éditez `backend/.env` (copié depuis `.env.example`) et **définissez impérativement une vraie clé
secrète** avant toute mise en production :

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Collez la valeur générée dans `VULNASSIST_SECRET_KEY=` du fichier `.env`.

### 7. Lancer l'application

```bash
cd ../backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 8. Accès depuis le navigateur

Depuis le serveur : `http://localhost:8000`
Depuis un autre poste du réseau interne : `http://<nom-ou-ip-du-serveur>:8000`

## Configuration

Toutes les options se règlent par variables d'environnement (préfixe `VULNASSIST_`) ou dans
`backend/.env` — voir `backend/.env.example` pour la liste complète et les valeurs par défaut
(base de données, clé secrète JWT, durée de session, admin par défaut, origines CORS pour le mode
développement).

## Lancement

En production, un seul processus suffit :

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

ou, de façon équivalente, `./scripts/start.ps1` / `./scripts/start.sh`.

Pour exécuter VulnAssist comme service Windows persistant, encapsulez la commande ci-dessus avec
[NSSM](https://nssm.cc/) ou le Planificateur de tâches (déclencheur "au démarrage du système").
Sous Linux, utilisez un service `systemd` classique appelant `scripts/start.sh`.

## Utilisation

1. Connectez-vous avec un compte **Administrateur** ou **Analyste sécurité**.
2. Rendez-vous dans **Import Tenable** et chargez le classeur Excel exporté depuis Tenable
   (la feuille `Vulnérabilités` est requise ; les feuilles `Analyse des tags des actifs` et
   `Décommissionés` sont utilisées si présentes pour enrichir le contexte des actifs).
3. Chaque ligne importée est automatiquement :
   - rattachée à un actif (créé ou mis à jour) ;
   - notée selon le moteur **CAA** (CVSS + exposition réseau + criticité de l'actif +
     exploitabilité, pondérations configurables dans **Règles CAA / SLE**) ;
   - associée à un délai de remédiation **SLE** selon sa sévérité CAA ;
   - attribuée à une équipe selon les **règles de propriété** (motifs sur le hostname / OS) ;
   - vérifiée contre les **exceptions** actives.
4. Le **tableau de bord** et les pages **Findings**, **Actifs**, **Remédiation groupée**,
   **Exceptions** et **Décommissionnés** permettent de piloter le traitement.
5. **Exports Excel** génère des classeurs (findings détaillés, synthèse KPI) pour diffusion hors
   application.

## Développement

Backend (rechargement automatique) :
```bash
cd backend
.venv\Scripts\activate  # ou source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Frontend (serveur de développement Vite, avec proxy vers l'API sur :8000) :
```bash
cd frontend
npm run dev
```

Ouvrez `http://localhost:5173`. Les appels `/api/*` sont automatiquement redirigés vers le backend
local (voir `frontend/vite.config.ts`).

## Tests

```bash
cd backend
.venv\Scripts\activate  # ou source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

Les tests couvrent le moteur CAA, le moteur SLE, le moteur d'attribution d'équipe, l'import Excel
(parsing + bout en bout via l'API), et l'authentification/RBAC.

## Migration vers PostgreSQL

La V1 fonctionne entièrement avec SQLite et ne nécessite aucun serveur de base de données
additionnel. Si le volume ou la concurrence l'exigent plus tard :

1. Installez PostgreSQL 14+ et créez une base `vulnassist`.
2. Dans `backend/.env`, définissez :
   ```
   VULNASSIST_DATABASE_URL=postgresql+psycopg2://vulnassist:motdepasse@localhost:5432/vulnassist
   ```
3. Appliquez les migrations sur la nouvelle base :
   ```bash
   alembic upgrade head
   python -m app.seed
   ```

Les modèles SQLAlchemy (`backend/app/models/`) sont écrits sans fonctionnalité spécifique à
SQLite, ce qui rend cette bascule directe.

## Sauvegarde

```powershell
.\scripts\backup.ps1
```
```bash
./scripts/backup.sh
```

Copie la base SQLite (`data/vulnassist.db`) vers `data/backups/` avec un horodatage. Si vous
utilisez PostgreSQL, utilisez `pg_dump` selon vos procédures habituelles.

## Rôles et permissions

| Rôle | Permissions |
|---|---|
| **Administrateur** | Gestion complète : utilisateurs, équipes, règles CAA/SLE/propriété, exceptions, décommissionnement, import, export. |
| **Analyste sécurité** | Import des scans, gestion des findings, création d'actions de remédiation, consultation des tableaux de bord, exports. |
| **Gestionnaire d'équipe** | Consultation en lecture des findings/KPI de son équipe uniquement. |
| **Lecture seule** | Consultation uniquement, sans droit de modification. |

L'authentification est **locale** (comptes stockés en base, mots de passe hachés en **Argon2id**).
Aucune intégration Microsoft Entra ID / Azure AD n'est utilisée ou prévue pour la V1.

## Structure du projet

```
vulnassist/
├── backend/
│   ├── app/
│   │   ├── api/routes/       endpoints REST (auth, findings, rules, exceptions, kpi, exports…)
│   │   ├── core/              configuration, base de données, sécurité (JWT/Argon2), RBAC
│   │   ├── models/            entités SQLAlchemy
│   │   ├── schemas/           schémas Pydantic
│   │   ├── services/          orchestration métier (import, scoring, KPI, remédiation…)
│   │   ├── rules/              moteurs purs : caa/ sle/ ownership/ exceptions/ remediation/
│   │   ├── importers/tenable_excel/   parseur du classeur Tenable
│   │   ├── exporters/         générateur de classeurs Excel de sortie
│   │   └── main.py            point d'entrée FastAPI (sert aussi le frontend compilé)
│   ├── alembic/                migrations de schéma
│   └── tests/
├── frontend/
│   └── src/
│       ├── pages/              une page par domaine fonctionnel
│       ├── components/, layouts/, hooks/, services/, types/
├── data/                       base SQLite + sauvegardes (non versionné)
├── scripts/                    install.ps1 / start.ps1 / backup.ps1 (+ équivalents .sh)
└── config/
```

Le dossier `data/` et tout export contenant des données réelles de vulnérabilités sont exclus du
dépôt Git (voir `.gitignore`) et ne doivent jamais y être poussés.
