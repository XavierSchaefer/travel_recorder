# T-AIA-911-NCY_3 ? NLP extraction gares (d?part / arriv?e)

Projet NLP en 3 parties : **pr?paration** (spaCy), **repr?sentation** (BERT/CamemBERT), **extraction** (NER DEP/ARR).  
Entr?e : une phrase. Sortie : gare de d?part et gare d?arriv?e, ou `invalid`.

? **Sch�ma de l'architecture :** [SCHEMA.md](SCHEMA.md)

## Dataset

- `data/dataset.csv` : colonnes `sentence`, `arrival`, `departure`, `nlp_tuple` (entit?s DEP/ARR avec positions).

## Environnement virtuel (venv)

Créer et activer un venv dans le projet :

**Windows (PowerShell) :**
```powershell
cd T-AIA-911-NCY_3
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (cmd) :**
```cmd
cd T-AIA-911-NCY_3
python -m venv venv
venv\Scripts\activate.bat
```

**Linux / macOS :**
```bash
cd T-AIA-911-NCY_3
python3 -m venv venv
source venv/bin/activate
```

Une fois activé, le prompt affiche `(venv)`.

## Installation

```bash
pip install -r requirements.txt
python -m spacy download fr_core_news_sm
```

## Utilisation

1. **Entra?ner le NER** (une fois) :
   ```bash
   python train_ner.py
   ```
   Cr?e le dossier `model_ner/`.

2. **Lancer l?extraction** (phrase au clavier) :
   ```bash
   python extract_gares.py
   ```
   Puis taper une phrase ; affichage : `d?part | arriv?e` ou `invalid`.

3. **Une phrase en argument** :
   ```bash
   python extract_gares.py "je veux aller de Paris ? Lyon"
   ```

## Les 3 parties NLP (dans `extract_gares.py`)

1. **Pr?-traitement** : tokenization et nettoyage avec spaCy (`partie1_preparation`).
2. **Repr?sentation** : encodage de la phrase avec CamemBERT (`partie2_representation`).
3. **Extraction** : NER (mod?le entra?n? sur le dataset) pour obtenir les gares DEP et ARR (`partie3_extraction`).

Si une sortie serait en anglais ou la phrase n?est pas une demande de trajet valide, le programme renvoie `invalid`.
