# Schéma de l'architecture

Architecture en **3 parties** : préparation (spaCy) → représentation (BERT/CamemBERT) → extraction (NER).

---

## Vue globale (données → entraînement → inférence)

```
┌──────────────────┐         ┌───────────────────┐         ┌────────────────────┐
│  data/dataset    │         │   train_ner.py     │         │  extract_gares.py  │
│  dataset.csv     │ ──────► │   entraîne NER     │ ──────► │  inférence         │
│  sentence,       │         │   DEP + ARR        │         │  Partie 1 → 2 → 3  │
│  arrival,        │         │   sauvegarde       │         │                    │
│  departure,      │         │   model_ner/       │         │  départ | arrivée │
│  nlp_tuple       │         │                    │         │  ou invalid        │
└──────────────────┘         └───────────────────┘         └────────────────────┘
```

---

## Flux dans extract_gares.py (une phrase)

```
                    phrase (texte brut)
                            │
                            ▼
              ┌─────────────────────────────┐
              │  est_phrase_invalide ?       │
              │  (vide / pas mot-clé trajet) │
              └─────────────────────────────┘
                     │              │
                    oui             non
                     │              │
                     ▼              ▼
              ┌──────────┐   ┌─────────────────────────────────────────────────────┐
              │ invalid  │   │  PARTIE 1 : Préparation (spaCy)                   │
              └──────────┘   │  partie1_preparation(phrase) → doc, tokens         │
                             └─────────────────────────────────────────────────────┘
                                                        │
                                                        ▼
                             ┌─────────────────────────────────────────────────────┐
                             │  PARTIE 2 : Représentation (CamemBERT)               │
                             │  partie2_representation(phrase) → vecteurs BERT      │
                             └─────────────────────────────────────────────────────┘
                                                        │
                                                        ▼
                             ┌─────────────────────────────────────────────────────┐
                             │  PARTIE 3 : Extraction (NER)                        │
                             │  partie3_extraction(doc) → depart, arrivee           │
                             └─────────────────────────────────────────────────────┘
                                                        │
                                                        ▼
                             ┌─────────────────────────────┐
                             │  depart et arrivee trouvés ? │
                             └─────────────────────────────┘
                                │                    │
                               non                   oui
                                │                    │
                                ▼                    ▼
                         ┌──────────┐         ┌─────────────────┐
                         │ invalid  │         │ depart | arrivee │
                         └──────────┘         └─────────────────┘
```

---

## Les 3 parties (détail)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PARTIE 1 – Préparation                                                      │
│  spaCy (fr_core_news_sm)                                                     │
│  • strip, tokenization                                                       │
│  • sortie : doc, tokens                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PARTIE 2 – Représentation                                                    │
│  CamemBERT (tokenizer + model)                                                │
│  • phrase → IDs → last_hidden_state (vecteurs par token)                      │
│  • sortie : tenseur (pour évolution future, ex. classif intention)           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PARTIE 3 – Extraction                                                       │
│  NER entraîné (model_ner/)                                                   │
│  • doc.text → entités DEP, ARR                                               │
│  • sortie : gare de départ, gare d'arrivée                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Dépendances

```
extract_gares.py
    │
    ├── spacy (fr_core_news_sm)  → Partie 1
    ├── torch + transformers     → Partie 2 (CamemBERT)
    └── model_ner/ (spaCy NER)   → Partie 3

train_ner.py
    │
    ├── spacy (fr_core_news_sm)
    └── pandas (dataset.csv)
```
