# -*- coding: utf-8 -*-
"""
NLP en 3 parties : entrée = phrase → sortie = gare de départ, gare d'arrivée (ou invalid).
Partie 1 : Préparation (spaCy). Partie 2 : Représentation (BERT/CamemBERT). Partie 3 : Extraction (NER).
"""
from pathlib import Path

# --- Partie 1 : Pré-traitement (tokenization, nettoyage) avec spaCy ---
def partie1_preparation(phrase, nlp_spacy):
    """Tokenization et nettoyage de la phrase."""
    phrase = (phrase or "").strip()
    doc = nlp_spacy(phrase)
    tokens = [t.text for t in doc]
    return doc, tokens

# --- Partie 2 : Représentation avec BERT (CamemBERT) ---
def partie2_representation(phrase, tokenizer_bert, model_bert, device):
    """Encode la phrase avec BERT pour une représentation vectorielle."""
    enc = tokenizer_bert(
        phrase,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=128,
    )
    enc = {k: v.to(device) for k, v in enc.items()}
    with __import__("torch").no_grad():
        out = model_bert(**enc)
    return out.last_hidden_state

# --- Partie 3 : Extraction des gares (NER) ---
def partie3_extraction(doc, nlp_ner):
    """Extrait les entités DEP et ARR du document (NER)."""
    doc_ner = nlp_ner(doc.text)
    depart = None
    arrivee = None
    for ent in doc_ner.ents:
        if ent.label_ == "DEP":
            depart = ent.text.strip()
        elif ent.label_ == "ARR":
            arrivee = ent.text.strip()
    return depart, arrivee

def est_phrase_invalide(phrase):
    """Si la phrase est vide ou sans mot-clé de demande de trajet → invalide."""
    if not phrase or not str(phrase).strip():
        return True
    mots_fr = ["aller", "rendre", "trains", "depuis", "partant", "gare", "à", "de", "je", "veux", "voudrais", "comment", "il y a"]
    phrase_lower = phrase.lower()
    if any(m in phrase_lower for m in mots_fr):
        return False
    return True

def traiter_phrase(phrase, nlp_spacy, nlp_ner, tokenizer_bert, model_bert, device):
    """Une phrase → départ | arrivée ou invalid."""
    if est_phrase_invalide(phrase):
        return "invalid"
    doc, _ = partie1_preparation(phrase, nlp_spacy)
    _ = partie2_representation(phrase, tokenizer_bert, model_bert, device)
    depart, arrivee = partie3_extraction(doc, nlp_ner)
    if depart is None or arrivee is None:
        return "invalid"
    return {
        "depart":depart,
        "arrivee":arrivee
    }


import spacy
import torch
from transformers import AutoTokenizer, AutoModel

base = Path(__file__).parent
model_ner_path = base / "model_ner"

try:
    nlp_spacy = spacy.load("fr_core_news_sm")
except OSError:
    print("Téléchargement du modèle spaCy français : fr_core_news_sm")
    spacy.cli.download("fr_core_news_sm")
    nlp_spacy = spacy.load("fr_core_news_sm")


nlp_ner = spacy.load(model_ner_path)

device = "cuda" if torch.cuda.is_available() else "cpu"
tokenizer_bert = AutoTokenizer.from_pretrained("camembert-base")
model_bert = AutoModel.from_pretrained("camembert-base").to(device)
model_bert.eval()


def extract_stations(phrase):
    station_dict = traiter_phrase(phrase, nlp_spacy, nlp_ner, tokenizer_bert, model_bert, device)
    print('station dict',station_dict)
    if station_dict != 'invalid' :
        if station_dict['depart'] and station_dict['arrivee']:
            trip_information = {
                "raw_input_depart":station_dict['depart'],
                "raw_input_arrivee":station_dict['arrivee']
            }
            return trip_information
        elif station_dict['arrivee'] == None: 
            return "Nous n'avons pas detecté la gare d'arrivée"
        elif station_dict['depart'] == None: 
            return "Nous n'avons pas detecté la gare de depart"
    return "La phrase n'est pas valide"

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        phrase = " ".join(sys.argv[1:])
        import spacy
        import torch
        from transformers import AutoTokenizer, AutoModel
        base = Path(__file__).parent
        model_ner_path = base / "model_ner"
        nlp_spacy = spacy.load("fr_core_news_sm")
        nlp_ner = spacy.load(model_ner_path)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        tokenizer_bert = AutoTokenizer.from_pretrained("camembert-base")
        model_bert = AutoModel.from_pretrained("camembert-base").to(device)
        model_bert.eval()
        print(traiter_phrase(phrase, nlp_spacy, nlp_ner, tokenizer_bert, model_bert, device))
    
