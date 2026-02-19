#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz


def normalize(text: str) -> str:
    text = (text or "").strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[\s\-_'’]+", " ", text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def ensure_spacy_model() -> None:
    import spacy

    try:
        spacy.load("fr_core_news_sm")
    except OSError:
        subprocess.run([sys.executable, "-m", "spacy", "download", "fr_core_news_sm"], check=True)


def ensure_baptiste_model(repo_root: Path) -> None:
    model_dir = repo_root / "back" / "model_ner"
    if model_dir.exists():
        return
    subprocess.run([sys.executable, str(repo_root / "back" / "train_ner.py")], check=True, cwd=str(repo_root))


def ensure_stanza_model() -> None:
    import stanza

    stanza.download("fr", processors="tokenize", verbose=False)


def load_gold(dataset_path: Path) -> list[dict[str, str]]:
    df = pd.read_csv(dataset_path, encoding="utf-8")
    records = []
    for _, row in df.iterrows():
        records.append(
            {
                "sentence": str(row["sentence"]).strip(),
                "depart": str(row["departure"]).strip(),
                "arrivee": str(row["arrival"]).strip(),
            }
        )
    return records


def evaluate_predictions(name: str, gold_rows: list[dict], predict_func) -> tuple[dict, list[dict]]:
    dep_ok = 0
    arr_ok = 0
    pair_ok = 0
    invalid_count = 0
    dep_sim_sum = 0.0
    arr_sim_sum = 0.0
    details = []

    for row in gold_rows:
        pred = predict_func(row["sentence"])
        if not pred or pred == "invalid":
            pred_dep = ""
            pred_arr = ""
            invalid_count += 1
        else:
            pred_dep = str(pred.get("depart", "")).strip()
            pred_arr = str(pred.get("arrivee", "")).strip()

        gold_dep = row["depart"]
        gold_arr = row["arrivee"]

        dep_match = normalize(pred_dep) == normalize(gold_dep)
        arr_match = normalize(pred_arr) == normalize(gold_arr)
        pair_match = dep_match and arr_match

        dep_ok += int(dep_match)
        arr_ok += int(arr_match)
        pair_ok += int(pair_match)

        dep_sim = fuzz.ratio(normalize(pred_dep), normalize(gold_dep))
        arr_sim = fuzz.ratio(normalize(pred_arr), normalize(gold_arr))
        dep_sim_sum += dep_sim
        arr_sim_sum += arr_sim

        details.append(
            {
                "sentence": row["sentence"],
                "gold_depart": gold_dep,
                "gold_arrivee": gold_arr,
                "pred_depart": pred_dep,
                "pred_arrivee": pred_arr,
                "dep_match": dep_match,
                "arr_match": arr_match,
                "pair_match": pair_match,
            }
        )

    n = len(gold_rows)
    metrics = {
        "parser": name,
        "samples": n,
        "invalid_predictions": invalid_count,
        "departure_accuracy": round(dep_ok / n, 4),
        "arrival_accuracy": round(arr_ok / n, 4),
        "pair_accuracy": round(pair_ok / n, 4),
        "departure_similarity_avg": round(dep_sim_sum / n, 2),
        "arrival_similarity_avg": round(arr_sim_sum / n, 2),
    }
    return metrics, details


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare Baptiste NLP parser vs Stanza parser")
    parser.add_argument("--dataset", default="back/database/dataset.csv")
    parser.add_argument("--res-csv", default="back/database/res.csv")
    parser.add_argument("--output-json", default="reports/nlp_parser_comparison.json")
    parser.add_argument("--output-md", default="reports/nlp_parser_comparison.md")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    dataset_path = (repo_root / args.dataset).resolve()
    res_csv_path = (repo_root / args.res_csv).resolve()
    out_json = (repo_root / args.output_json).resolve()
    out_md = (repo_root / args.output_md).resolve()
    out_json.parent.mkdir(parents=True, exist_ok=True)

    ensure_spacy_model()
    ensure_baptiste_model(repo_root)
    ensure_stanza_model()

    sys.path.insert(0, str(repo_root))
    from back import extract_gares  # noqa: E402
    from back.parser_stanza_rules import build_stanza_rule_parser, parse_with_stanza_rules  # noqa: E402

    gold_rows = load_gold(dataset_path)
    stanza_nlp, normalized_to_canonical, station_keys = build_stanza_rule_parser(res_csv_path)

    def predict_baptiste(sentence: str):
        pred = extract_gares.traiter_phrase(
            sentence,
            extract_gares.nlp_spacy,
            extract_gares.nlp_ner,
            extract_gares.tokenizer_bert,
            extract_gares.model_bert,
            extract_gares.device,
        )
        return pred

    def predict_stanza_rules(sentence: str):
        return parse_with_stanza_rules(sentence, stanza_nlp, normalized_to_canonical, station_keys)

    baptiste_metrics, baptiste_details = evaluate_predictions("baptiste_spacy_camembert_ner", gold_rows, predict_baptiste)
    stanza_rules_metrics, stanza_rules_details = evaluate_predictions("stanza_rule_based_parser", gold_rows, predict_stanza_rules)

    payload = {
        "dataset": str(dataset_path),
        "res_csv": str(res_csv_path),
        "metrics": [baptiste_metrics, stanza_rules_metrics],
        "notes": "Evaluation on available dataset.csv (60 lines).",
        "details": {
            "baptiste": baptiste_details,
            "stanza_rules": stanza_rules_details,
        },
    }

    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# Comparaison des parseurs NLP")
    md.append("")
    md.append(f"- Dataset: `{dataset_path}`")
    md.append(f"- Taille: `{len(gold_rows)}` phrases")
    md.append("")
    md.append("| Parseur | Samples | Invalid | Dep Acc | Arr Acc | Pair Acc | Dep Sim | Arr Sim |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for m in payload["metrics"]:
        md.append(
            f"| {m['parser']} | {m['samples']} | {m['invalid_predictions']} | "
            f"{m['departure_accuracy']:.4f} | {m['arrival_accuracy']:.4f} | "
            f"{m['pair_accuracy']:.4f} | {m['departure_similarity_avg']:.2f} | {m['arrival_similarity_avg']:.2f} |"
        )
    md.append("")
    md.append("## Lecture rapide")
    md.append("- `pair_accuracy`: exact match simultané départ + arrivée.")
    md.append("- `Dep/Arr Sim`: similarité moyenne texte normalisé (RapidFuzz ratio).")
    md.append("")
    out_md.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"output_json={out_json}")
    print(f"output_md={out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
