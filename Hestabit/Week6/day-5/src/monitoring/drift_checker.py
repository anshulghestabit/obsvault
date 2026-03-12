from pathlib import Path
import json

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
TRAIN_DATA_PATH = BASE_DIR / "data" / "processed" / "final.csv"
CURRENT_DATA_PATH = BASE_DIR / "data" / "processed" / "final.csv"
OUTPUT_PATH = BASE_DIR / "monitoring" / "drift_report.json"


def compute_numeric_means(df: pd.DataFrame) -> pd.Series:
    numeric_df = df.select_dtypes(include=["number"]).drop(columns=["SalePrice"], errors="ignore")
    return numeric_df.mean()


def main():
    train_df = pd.read_csv(TRAIN_DATA_PATH)
    current_df = pd.read_csv(CURRENT_DATA_PATH)

    train_means = compute_numeric_means(train_df)
    current_means = compute_numeric_means(current_df)

    drift_report = {}

    for col in train_means.index:
        train_mean = train_means[col]
        current_mean = current_means.get(col, None)

        if pd.isna(train_mean) or current_mean is None or pd.isna(current_mean):
            continue

        abs_diff = abs(current_mean - train_mean)
        pct_diff = abs_diff / (abs(train_mean) + 1e-8)

        drift_report[col] = {
            "train_mean": round(float(train_mean), 4),
            "current_mean": round(float(current_mean), 4),
            "absolute_difference": round(float(abs_diff), 4),
            "percent_difference": round(float(pct_diff), 4),
            "drift_flag": bool(pct_diff > 0.10),
        }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(drift_report, f, indent=4)

    print(f"Drift report saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()