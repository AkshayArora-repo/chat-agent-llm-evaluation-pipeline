#!/usr/bin/env python3
"""Split labeled_traces.csv into stratified train/dev/test sets.

Ratios: train 15%, dev 40%, test 45%.
Stratified by label to keep PASS/FAIL proportional in each set.
"""

import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

TRAIN_RATIO = 0.15
DEV_RATIO = 0.40
TEST_RATIO = 0.45
RANDOM_STATE = 42


def main():
    hw3_dir = Path(__file__).resolve().parent.parent
    data_dir = hw3_dir / "data"

    input_path = data_dir / "labeled_traces.csv"
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} traces from {input_path.name}")
    print(f"  PASS: {(df['label']=='PASS').sum()}, FAIL: {(df['label']=='FAIL').sum()}")

    # Stage 1: split train (15%) from the rest (85%)
    train_df, temp_df = train_test_split(
        df,
        test_size=(DEV_RATIO + TEST_RATIO),
        stratify=df["label"],
        random_state=RANDOM_STATE,
    )

    # Stage 2: split remainder into dev and test
    dev_proportion = DEV_RATIO / (DEV_RATIO + TEST_RATIO)
    dev_df, test_df = train_test_split(
        temp_df,
        test_size=(1 - dev_proportion),
        stratify=temp_df["label"],
        random_state=RANDOM_STATE,
    )

    # Validate
    for name, split_df in [("train", train_df), ("dev", dev_df), ("test", test_df)]:
        labels = set(split_df["label"].unique())
        assert "PASS" in labels and "FAIL" in labels, f"{name} missing a label: {labels}"
    assert len(train_df) + len(dev_df) + len(test_df) == len(df), "Row count mismatch"

    # Save
    train_df.to_csv(data_dir / "train_set.csv", index=False)
    dev_df.to_csv(data_dir / "dev_set.csv", index=False)
    test_df.to_csv(data_dir / "test_set.csv", index=False)

    # Summary
    print(f"\n{'Set':<8} {'Total':>6} {'PASS':>6} {'FAIL':>6} {'Fail%':>7}")
    print("-" * 35)
    for name, split_df in [("train", train_df), ("dev", dev_df), ("test", test_df)]:
        total = len(split_df)
        p = (split_df["label"] == "PASS").sum()
        f = (split_df["label"] == "FAIL").sum()
        print(f"{name:<8} {total:>6} {p:>6} {f:>6} {f/total*100:>6.1f}%")
    print("-" * 35)
    print(f"{'total':<8} {len(df):>6}")

    # Show dietary restriction coverage in train
    print(f"\nTrain dietary restrictions ({train_df['dietary_restriction'].nunique()} categories):")
    for diet, count in train_df["dietary_restriction"].value_counts().items():
        print(f"  {diet}: {count}")

    print(f"\nSaved to: train_set.csv, dev_set.csv, test_set.csv")


if __name__ == "__main__":
    main()
