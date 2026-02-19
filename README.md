# Travel Recorder

Application Dash pour extraire les gares de départ/arrivée depuis une phrase en français et tracer l'itinéraire sur une carte.

## Prérequis
- Python 3.10+ installé
- `git` (optionnel, pour cloner le repo)

## Installation rapide
1) Cloner le projet (ou télécharger l'archive) puis se placer à la racine:
```bash
cd travel_recorder
```
2) Créer et activer un environnement virtuel:
- macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```
- Windows (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
3) Installer les dépendances (inclut le modèle spaCy `fr_core_news_sm` via la roue fournie):
```bash
pip install -r requirements.txt
```

## Préparer les données
Le fichier `res.csv` externe (fourni par l'équipe) doit être copié dans le dossier `back/database/` avant de lancer l'appli:
```bash
cp /chemin/vers/res.csv back/database/res.csv
```
Le repo contient déjà un exemple, mais écrasez-le si vous avez une version à jour.

## Lancer l'application
Depuis l'environnement virtuel activé:
```bash
python main.py
```
L'interface Dash est accessible sur http://localhost:8090/.

## Utilisation
- Renseigner une phrase type « je veux aller de Paris à Lyon » ou sélectionner manuellement Départ/Arrivée via les menus déroulants.
- Le trajet le plus court est affiché sur la carte et la durée estimée est indiquée.

## Arborescence utile
- `main.py` : point d'entrée Dash.
- `back/` : logique NLP (extraction d'entités, Dijkstra, datasets).
- `back/database/res.csv` : données des gares; `dataset.csv` : dataset d'entraînement.

## Dépannage
- Si `fr_core_news_sm` est manquant, réinstallez les deps: `pip install -r requirements.txt`.
- Vérifiez que l'environnement virtuel est bien activé avant de lancer `python main.py`.
