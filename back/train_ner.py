# -*- coding: utf-8 -*-
"""
Entraînement du modèle NER spaCy à partir du dataset (DEP, ARR).
À lancer une fois pour générer le modèle model_ner/ 
"""
import re
import spacy
from spacy.training import Example
import pandas as pd
from pathlib import Path

def parser_nlp_tuple(nlp_tuple_str):
    """Extrait les entités (start, end, label) depuis la chaîne nlp_tuple."""
    entities = []
    # Pattern: (nombre, nombre, 'DEP') ou (nombre, nombre, 'ARR')
    for m in re.finditer(r"\((\d+),\s*(\d+),\s*['\"](\w+)['\"]\)", nlp_tuple_str):
        start, end, label = int(m.group(1)), int(m.group(2)), m.group(3)
        if label in ("DEP", "ARR"):
            entities.append((start, end, label))
    return entities

def main():
    data_path = Path(__file__).parent / "database" / "dataset.csv"
    df = pd.read_csv(data_path, encoding="utf-8")
    # Charger le modèle français de base (sans NER personnalisé au départ)
    nlp = spacy.load("fr_core_news_sm")
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner")
    else:
        ner = nlp.get_pipe("ner")
    ner.add_label("DEP")
    ner.add_label("ARR")

    train_data = []
    for _, row in df.iterrows():
        phrase = row["sentence"]
        if pd.isna(phrase) or not str(phrase).strip():
            continue
        phrase = str(phrase).strip()
        ent = parser_nlp_tuple(str(row["nlp_tuple"]))
        if not ent:
            continue
        train_data.append((phrase, {"entities": [(s, e, l) for s, e, l in ent]}))

    import random
    random.seed(42)
    other_pipes = [p for p in nlp.pipe_names if p != "ner"]
    with nlp.disable_pipes(*other_pipes):
        n_iter = 25
        optimizer = nlp.begin_training()
        for it in range(n_iter):
            random.shuffle(train_data)
            for text, annotations in train_data:
                doc = nlp.make_doc(text)
                example = Example.from_dict(doc, annotations)
                nlp.update([example], sgd=optimizer)

    out_dir = Path(__file__).parent / "model_ner"
    out_dir.mkdir(exist_ok=True)
    nlp.to_disk(out_dir)
    print("Modèle NER enregistré dans", out_dir)

if __name__ == "__main__":
    main()
