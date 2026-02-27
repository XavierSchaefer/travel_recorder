# Comparaison des parseurs NLP

- Dataset: `/home/kudovic/Desktop/EPITECH/TOR/Xavier/back/database/dataset_test.csv`
- Taille: `12` phrases

| Parseur | Samples | Invalid | Dep Acc | Arr Acc | Pair Acc | Dep Sim | Arr Sim |
|---|---:|---:|---:|---:|---:|---:|---:|
| baptiste_spacy_camembert_ner | 12 | 1 | 0.9167 | 0.8333 | 0.8333 | 91.67 | 88.89 |
| stanza_rule_based_parser | 12 | 1 | 0.9167 | 0.9167 | 0.9167 | 91.67 | 91.67 |

## Lecture rapide
- `pair_accuracy`: exact match simultané départ + arrivée.
- `Dep/Arr Sim`: similarité moyenne texte normalisé (RapidFuzz ratio).

