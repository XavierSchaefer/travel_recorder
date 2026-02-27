#!/usr/bin/env python3
import argparse
from pathlib import Path

import pandas as pd


def main() -> int:
    parser = argparse.ArgumentParser(description="Create deterministic train/test split for NLP dataset.")
    parser.add_argument("--input", default="back/database/dataset.csv")
    parser.add_argument("--train-output", default="back/database/dataset_train.csv")
    parser.add_argument("--test-output", default="back/database/dataset_test.csv")
    parser.add_argument("--test-ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    input_path = Path(args.input)
    train_path = Path(args.train_output)
    test_path = Path(args.test_output)

    df = pd.read_csv(input_path, encoding="utf-8")
    if df.empty:
        raise ValueError("Input dataset is empty.")

    test_count = max(1, int(round(len(df) * args.test_ratio)))
    shuffled = df.sample(frac=1.0, random_state=args.seed).reset_index(drop=True)
    test_df = shuffled.iloc[:test_count].copy()
    train_df = shuffled.iloc[test_count:].copy()

    train_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.parent.mkdir(parents=True, exist_ok=True)
    train_df.to_csv(train_path, index=False, encoding="utf-8")
    test_df.to_csv(test_path, index=False, encoding="utf-8")

    print(f"input={input_path}")
    print(f"train={train_path} rows={len(train_df)}")
    print(f"test={test_path} rows={len(test_df)}")
    print(f"seed={args.seed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
