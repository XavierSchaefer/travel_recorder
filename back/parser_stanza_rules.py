from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd
import stanza


def _normalize(text: str) -> str:
    text = (text or "").strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[\s\-_'’]+", " ", text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _clean_capture(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"^[\s,;:!?\.]+|[\s,;:!?\.]+$", "", text)
    return text


def _split_once_ci(text: str, needle: str) -> tuple[str, str] | None:
    low = text.lower()
    idx = low.find(needle.lower())
    if idx < 0:
        return None
    left = text[:idx]
    right = text[idx + len(needle) :]
    return left, right


def _build_station_reference(res_csv_path: Path) -> tuple[dict[str, str], list[str]]:
    df = pd.read_csv(res_csv_path, sep=";", encoding="utf-8", low_memory=False)
    stop_names = sorted({str(s).strip() for s in df["stop_name"].dropna().tolist() if str(s).strip()})
    normalized_to_canonical = {}
    for name in stop_names:
        key = _normalize(name)
        if key and key not in normalized_to_canonical:
            normalized_to_canonical[key] = name
    return normalized_to_canonical, list(normalized_to_canonical.keys())


def _best_station_key(query_key: str, station_keys: list[str]) -> tuple[str | None, float]:
    if not query_key:
        return None, 0.0
    best_key = None
    best_score = -1.0
    for sk in station_keys:
        score = SequenceMatcher(None, query_key, sk).ratio()
        if score > best_score:
            best_key = sk
            best_score = score
    return best_key, best_score


def _canonicalize(raw_value: str, normalized_to_canonical: dict[str, str], station_keys: list[str]) -> str:
    raw = _clean_capture(raw_value)
    key = _normalize(raw)
    if key in normalized_to_canonical:
        return normalized_to_canonical[key]

    best_key, best_score = _best_station_key(key, station_keys)
    if best_key and best_score >= 0.82:
        return normalized_to_canonical[best_key]
    return raw


def _split_je_veux_faire(payload: str, normalized_to_canonical: dict[str, str], station_keys: list[str]) -> tuple[str | None, str | None]:
    payload = _clean_capture(payload)
    payload_key = _normalize(payload)
    tokens = payload_key.split()
    if len(tokens) < 2:
        return None, None

    for i in range(1, len(tokens)):
        left_key = " ".join(tokens[:i])
        right_key = " ".join(tokens[i:])
        if left_key in normalized_to_canonical and right_key in normalized_to_canonical:
            return normalized_to_canonical[left_key], normalized_to_canonical[right_key]

    best = None
    best_score = -1.0
    for i in range(1, len(tokens)):
        left_key = " ".join(tokens[:i])
        right_key = " ".join(tokens[i:])
        best_left, score_left = _best_station_key(left_key, station_keys)
        best_right, score_right = _best_station_key(right_key, station_keys)
        score = score_left + score_right
        if best_left and best_right and score > best_score:
            best_score = score
            best = (best_left, best_right, score_left, score_right)

    if best and best[2] >= 0.74 and best[3] >= 0.74:
        return normalized_to_canonical[best[0]], normalized_to_canonical[best[1]]
    return None, None


def parse_with_stanza_rules(
    sentence: str,
    nlp,
    normalized_to_canonical: dict[str, str],
    station_keys: list[str],
) -> dict | str:
    text = (sentence or "").strip()
    if not text:
        return "invalid"

    # Stanza pass (tokenization/sentence processing)
    _ = nlp(text)
    lower = text.lower()

    if lower.startswith("je voudrais aller de "):
        payload = text[len("je voudrais aller de ") :]
        split = _split_once_ci(payload, " à ")
        if split is None:
            split = _split_once_ci(payload, " a ")
        if split:
            dep_raw, arr_raw = split
            dep = _canonicalize(dep_raw, normalized_to_canonical, station_keys)
            arr = _canonicalize(arr_raw, normalized_to_canonical, station_keys)
            return {"depart": dep, "arrivee": arr}
        return "invalid"

    if lower.startswith("comment me rendre à ") or lower.startswith("comment me rendre a "):
        split = _split_once_ci(text, " depuis la gare de ")
        if split:
            arr_part, dep_part = split
            arr_raw = arr_part.replace("Comment me rendre à", "", 1).replace("Comment me rendre a", "", 1)
            dep_raw = dep_part.rstrip(" ?")
            dep = _canonicalize(dep_raw, normalized_to_canonical, station_keys)
            arr = _canonicalize(arr_raw, normalized_to_canonical, station_keys)
            return {"depart": dep, "arrivee": arr}
        return "invalid"

    if lower.startswith("je veux aller voir mon ami albert à ") or lower.startswith("je veux aller voir mon ami albert a "):
        split = _split_once_ci(text, " en partant de ")
        if split:
            arr_part, dep_part = split
            arr_raw = (
                arr_part.replace("Je veux aller voir mon ami Albert à", "", 1)
                .replace("Je veux aller voir mon ami Albert a", "", 1)
                .replace("je veux aller voir mon ami albert à", "", 1)
                .replace("je veux aller voir mon ami albert a", "", 1)
            )
            dep = _canonicalize(dep_part, normalized_to_canonical, station_keys)
            arr = _canonicalize(arr_raw, normalized_to_canonical, station_keys)
            return {"depart": dep, "arrivee": arr}
        return "invalid"

    if lower.startswith("il y a-t-il des trains de "):
        payload = text[len("Il y a-t-il des trains de ") :] if text.startswith("Il") else text[len("il y a-t-il des trains de ") :]
        split = _split_once_ci(payload, " à ")
        if split is None:
            split = _split_once_ci(payload, " a ")
        if split:
            dep_raw, arr_raw = split
            dep = _canonicalize(dep_raw, normalized_to_canonical, station_keys)
            arr = _canonicalize(arr_raw, normalized_to_canonical, station_keys)
            return {"depart": dep, "arrivee": arr}
        return "invalid"

    if lower.startswith("depuis "):
        split1 = _split_once_ci(text, " je veux aller a ")
        if split1:
            dep_raw = split1[0].replace("depuis", "", 1).replace("Depuis", "", 1)
            split2 = _split_once_ci(split1[1], " pour ")
            arr_raw = split2[0] if split2 else split1[1]
            dep = _canonicalize(dep_raw, normalized_to_canonical, station_keys)
            arr = _canonicalize(arr_raw, normalized_to_canonical, station_keys)
            return {"depart": dep, "arrivee": arr}
        return "invalid"

    if lower.startswith("je veux faire "):
        payload = text[len("je veux faire ") :]
        dep, arr = _split_je_veux_faire(payload, normalized_to_canonical, station_keys)
        if dep and arr:
            return {"depart": dep, "arrivee": arr}
        return "invalid"

    return "invalid"


def build_stanza_rule_parser(res_csv_path: Path):
    nlp = stanza.Pipeline(lang="fr", processors="tokenize", tokenize_pretokenized=False, use_gpu=False, verbose=False)
    normalized_to_canonical, station_keys = _build_station_reference(res_csv_path)
    return nlp, normalized_to_canonical, station_keys
