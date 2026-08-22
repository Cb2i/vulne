# Installation locale sur Windows

Guide pas a pas pour faire tourner l'agent XAUUSD.sc sur ton PC Windows (le
meme PC ou tourne MT4/PU Prime), en dehors de tout environnement restreint en
reseau.

## 1. Installer Python

1. Va sur https://www.python.org/downloads/ et telecharge la derniere version
   Python 3 (3.11 ou plus recent).
2. Lance l'installeur. **Important** : coche la case **"Add python.exe to PATH"**
   en bas de la premiere fenetre avant de cliquer sur "Install Now".
3. Verifie l'installation : ouvre PowerShell (touche Windows, tape
   `powershell`, Entree) et tape :
   ```
   python --version
   ```
   Tu dois voir quelque chose comme `Python 3.12.x`.

## 2. Telecharger le projet

Tant que le PR n'est pas encore fusionne dans `main`, telecharge la branche
directement :

1. Va sur https://github.com/Cb2i/vulne/archive/refs/heads/claude/xauusd-analysis-agent-o19hqy.zip
   (le telechargement du ZIP demarre automatiquement).
2. Dezippe le fichier telecharge (clic droit > "Extraire tout...").
3. Dans le dossier extrait, entre dans `vulne-claude-xauusd-analysis-agent-o19hqy`
   puis `xauusd-agent`. C'est ce dossier `xauusd-agent` qui contient le projet.

*Une fois le PR fusionne dans `main`, tu pourras simplement telecharger*
*https://github.com/Cb2i/vulne/archive/refs/heads/main.zip a la place.*

## 3. Ouvrir PowerShell dans le dossier du projet

Dans l'explorateur de fichiers Windows, ouvre le dossier `xauusd-agent`, puis :
- Maj + clic droit dans un espace vide du dossier > **"Ouvrir la fenetre PowerShell ici"**
  (ou "Ouvrir dans le terminal" selon la version de Windows).

## 4. Installer les dependances

Dans PowerShell, colle ces commandes une par une (Entree apres chacune) :

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Ta ligne de commande doit maintenant commencer par `(.venv)` : l'environnement
virtuel est actif.

*Si PowerShell refuse d'executer `activate` (erreur "l'execution de scripts est*
*desactivee"), ouvre PowerShell en administrateur et tape une fois :*
*`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, puis reessaie.*

## 5. Configurer tes cles API

```powershell
copy .env.example .env
notepad .env
```

Dans le Bloc-notes qui s'ouvre, remplis les lignes avec tes cles (deja
obtenues) :

```
TWELVE_DATA_API_KEY=de663173766b436e96e16b9cd582c641
FRED_API_KEY=1519e3e511797a5dc49435c6d31e1220
```

Enregistre (Ctrl+S) et ferme le Bloc-notes. Ce fichier `.env` reste
uniquement sur ton PC, il n'est jamais envoye nulle part par le projet.

## 6. Generer le rapport

Toujours dans la meme fenetre PowerShell (avec `(.venv)` actif) :

```powershell
python main.py daily
```

Le rapport s'affiche a l'ecran et est sauvegarde dans le dossier
`reports_out\`. Verifie que les sections "Technical Analysis", "DXY & Treasury
Yields", etc. affichent maintenant de vraies valeurs et non plus
"Donnee non disponible / non verifiable".

## 7. (Plus tard) Automatiser lundi-vendredi 06:30 et dimanche 10:00

Deux options :

- **Simple, PC toujours allume** : laisser tourner
  `python main.py schedule` dans une fenetre PowerShell en continu.
- **Recommande, via le Planificateur de taches Windows** : creer une tache
  planifiee qui execute, aux heures voulues (06:30 lun-ven, 10:00 dim),
  la commande :
  ```
  C:\chemin\vers\xauusd-agent\.venv\Scripts\python.exe C:\chemin\vers\xauusd-agent\main.py daily
  ```
  (remplace `C:\chemin\vers\xauusd-agent` par le chemin reel du dossier chez
  toi). Le Planificateur de taches se trouve dans le menu Demarrer en tapant
  "Planificateur de taches".

## En cas de probleme

- `python` non reconnu : reinstalle Python en cochant bien "Add to PATH", ou
  redemarre PowerShell apres l'installation.
- Rapport toujours avec "Donnee non disponible" partout : verifie que le
  fichier `.env` contient bien tes cles sans espace ni guillemets, et que
  PowerShell est bien dans le dossier `xauusd-agent` (tape `dir` : tu dois
  voir `main.py`).
- Erreur de connexion Twelve Data/FRED : verifie ta connexion internet et que
  les cles sont valides (teste-les directement sur twelvedata.com /
  fred.stlouisfed.org si besoin).
