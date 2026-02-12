import os
import sys
import re
import unicodedata
from rapidfuzz import fuzz

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)


from back import extract_gares 
from back.stations import get_station_candidates_by_raw_name, get_station_id_by_name
from back.path_finding import dijkstra


BAD_TOKENS = {"rue", "route", "eglise", "église", "avenue", "bd", "boulevard"}
GOOD_TOKENS = {"gare", "centre", "ville"}
def normalize(s: str) -> str:
    s = s.strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")  # remove accents
    s = re.sub(r"[-'’]", " ", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def best_station_match(query: str, candidates: list[str]) -> tuple[str, float]:
    q = normalize(query)

    # 1) exact match wins
    exact = [c for c in candidates if normalize(c) == q]
    if exact:
        return [exact[0]], [1.0]

    q_tokens = q.split()

    best = None
    best_score = -1.0
    cand_list = []
    scores_list = []
    for cand in candidates:
        c_norm = normalize(cand)
        c_tokens = c_norm.split()

        # base fuzzy similarity
        score = fuzz.WRatio(q, c_norm) / 100.0

        # 2) word-boundary bonus (metz as a full token)
        if q in c_tokens:
            score += 0.20

        # 3) prefix trap penalty (metz vs metzeral/metzing/metzervisse...)
        # if query is a prefix of first token but not a full token => penalize hard
        if c_tokens and c_tokens[0].startswith(q) and q not in c_tokens:
            score -= 0.35

        # 4) heuristic tokens
        if any(t in c_tokens for t in GOOD_TOKENS):
            score += 0.05
        if any(t in c_tokens for t in BAD_TOKENS):
            score -= 0.05

        if score > best_score:
            best_score = score
            best = cand
        cand_list.append(cand)
        scores_list.append(score)
    return cand_list, scores_list

def extract_stations_from_phrase(phrase):
    stations_dict = extract_gares.extract_stations(phrase)
    if type(stations_dict) == str:
        return stations_dict

    candidates_arrivee = get_station_candidates_by_raw_name(stations_dict['raw_input_arrivee'])
    if candidates_arrivee == ([],[]):
        return "La gare d'arrivée n'est pas valide"
    candidates_depart = get_station_candidates_by_raw_name(stations_dict['raw_input_depart'])
    if candidates_depart == ([],[]):
        return "La gare de départ n'est pas valide"
    
    gare_arrivee = best_station_match(stations_dict['raw_input_arrivee'], candidates_arrivee[1])
    id_arrivee = []
    for g in gare_arrivee[0]:
        id_arrivee.append(get_station_id_by_name(g))
    
    
    gare_depart = best_station_match(stations_dict['raw_input_depart'], candidates_depart[1])
    id_depart = []
    for g in gare_depart[0]:
        id_depart.append(get_station_id_by_name(g))

    trip_information = {
        "raw_input_depart":stations_dict['raw_input_depart'],
        "raw_input_arrivee":stations_dict['raw_input_arrivee'],
        "list_gare_arrivee":gare_arrivee[0],
        "list_gare_depart":gare_depart[0],
        "list_match_score_arrivee":gare_arrivee[1],
        "list_match_score_depart":gare_depart[1],
        "list_id_gare_arrivee":id_arrivee,
        "list_id_gare_depart":id_depart,
    }
    return trip_information

def phrase_to_trip(raw_phrase):
    #1. normalize phrase
    phrase = str(raw_phrase).lower()

    trip_info = extract_stations_from_phrase(phrase)
    print(trip_info)
    if type(trip_info) == str:
        return trip_info

    #find best trip
    trips_dict = {}
    for d_name, d_id, d_score in zip(trip_info['list_gare_depart'],trip_info['list_id_gare_depart'],trip_info['list_match_score_depart']) :
        for a_name, a_id, a_score in zip(trip_info['list_gare_arrivee'],trip_info['list_id_gare_arrivee'],trip_info['list_match_score_arrivee']) :
            path, total_s = dijkstra(d_id, a_id)
            trips_dict[total_s] = {
                'd_name':d_name,
                'd_id':d_id,
                'd_score':d_score,
                'a_name':a_name,
                'a_id':a_id,
                'a_score':a_score,
                'path':path,
                'total_s':total_s
            }

    return {
        'trip_info':trip_info,
        'best_trip':sorted(trips_dict.items())[0][1]
    }

#phrase_to_trip("Je veux aller de Paris a MEtz")
#print(phrase_to_trip("Je veux aller de Paris a MEtz"))


#Paris Est to Metz = 4980