"""Phase 1 - Step 4: Sampling weights and raw vs. weighted summaries.

Weight used: WTPH2YR (phlebotomy weight), because HbA1c is a blood analyte and the
analytic sample is restricted to participants with an HbA1c result (GHB_L documentation).

Inputs
------
data/processed/analytic_sample.csv

Outputs (reports/phase1/tables/)
--------------------------------
weight_summary.csv, weights_by_group.csv, raw_vs_weighted_numeric.csv,
raw_vs_weighted_categorical.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

from common import add_categories

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
TABLES_DIR = PROJECT_ROOT / "reports" / "phase1" / "tables"

WEIGHT_COL = "WTPH2YR"
NUMERIC_VARIABLES = [
    "RIDAGEYR", "LBXGH", "BMXBMI", "sleep_hours", "mvpa_min_week", "sedentary_hours",
]
CATEGORICAL_VARIABLES = [
    "sex", "age_group", "race_eth", "diabetes_dx", "bmi_cat", "sleep_cat",
]


def weighted_mean(x: pd.Series, w: pd.Series) -> float:
    return float(np.average(x, weights=w))


def weighted_sd(x: pd.Series, w: pd.Series) -> float:
    mu = weighted_mean(x, w)
    return float(np.sqrt(np.average((x - mu) ** 2, weights=w)))


def weighted_quantile(x: pd.Series, w: pd.Series, q: float) -> float:
    """Smallest value whose cumulative weight share reaches q."""
    order = np.argsort(x.to_numpy())
    xs = x.to_numpy()[order]
    cum = np.cumsum(w.to_numpy()[order]) / w.sum()
    return float(xs[min(np.searchsorted(cum, q), len(xs) - 1)])


def weight_summary(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    rows = []
    for col in columns:
        w = df[col]
        cv = w.std() / w.mean()
        rows.append(
            {
                "weight": col,
                "n": len(w),
                "min": w.min(),
                "median": w.median(),
                "max": w.max(),
                "max_to_min_ratio": w.max() / w.min(),
                "sum_millions": w.sum() / 1e6,
                "cv": cv,
                "kish_design_effect": 1 + cv ** 2,
                "effective_n": w.sum() ** 2 / (w ** 2).sum(),
            }
        )
    return pd.DataFrame(rows).round(2)


def weights_by_group(df: pd.DataFrame) -> pd.DataFrame:
    """Average weight, i.e. how many US adults one participant represents, by group."""
    total_weight = df[WEIGHT_COL].sum()
    parts = []
    for col in ["age_group", "race_eth", "sex"]:
        g = df.groupby(col, observed=True)[WEIGHT_COL]
        table = pd.DataFrame(
            {
                "n": g.size(),
                "mean_weight": g.mean().round(0),
                "population_millions": (g.sum() / 1e6).round(1),
                "pct_of_sample": (100 * g.size() / len(df)).round(1),
                "pct_of_population": (100 * g.sum() / total_weight).round(1),
            }
        ).reset_index().rename(columns={col: "group"})
        table.insert(0, "variable", col)
        parts.append(table)
    return pd.concat(parts, ignore_index=True)


def numeric_comparison(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in NUMERIC_VARIABLES:
        x, w = df[col], df[WEIGHT_COL]
        rows.append(
            {
                "variable": col,
                "raw_mean": x.mean(),
                "weighted_mean": weighted_mean(x, w),
                "raw_median": x.median(),
                "weighted_median": weighted_quantile(x, w, 0.5),
                "raw_sd": x.std(),
                "weighted_sd": weighted_sd(x, w),
            }
        )
    out = pd.DataFrame(rows)
    out["mean_difference"] = out["weighted_mean"] - out["raw_mean"]
    return out.round(2)


def categorical_comparison(df: pd.DataFrame) -> pd.DataFrame:
    parts = []
    total_w = df[WEIGHT_COL].sum()
    for col in CATEGORICAL_VARIABLES:
        raw = df[col].value_counts(normalize=True, sort=False) * 100
        weighted = df.groupby(col, observed=True)[WEIGHT_COL].sum() / total_w * 100
        table = pd.DataFrame({"raw_pct": raw, "weighted_pct": weighted}).reset_index()
        table = table.rename(columns={"index": "category", col: "category"})
        table["difference_pp"] = table["weighted_pct"] - table["raw_pct"]
        table.insert(0, "variable", col)
        parts.append(table)
    return pd.concat(parts, ignore_index=True).round(1)


def main() -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    df = add_categories(pd.read_csv(PROCESSED_DIR / "analytic_sample.csv"))

    w_summary = weight_summary(df, ["WTPH2YR", "WTMEC2YR"])
    by_group = weights_by_group(df)
    numeric = numeric_comparison(df)
    categorical = categorical_comparison(df)

    w_summary.to_csv(TABLES_DIR / "weight_summary.csv", index=False)
    by_group.to_csv(TABLES_DIR / "weights_by_group.csv", index=False)
    numeric.to_csv(TABLES_DIR / "raw_vs_weighted_numeric.csv", index=False)
    categorical.to_csv(TABLES_DIR / "raw_vs_weighted_categorical.csv", index=False)

    pd.set_option("display.width", 200)
    print("Weight summary (analytic sample):")
    print(w_summary.to_string(index=False))
    print(f"\nMean weight and represented population by group (weight = {WEIGHT_COL}):")
    print(by_group.to_string(index=False))
    print("\nRaw vs. weighted: quantitative variables")
    print(numeric.to_string(index=False))
    print("\nRaw vs. weighted: categorical variables (% of sample / population)")
    print(categorical.to_string(index=False))


if __name__ == "__main__":
    main()
