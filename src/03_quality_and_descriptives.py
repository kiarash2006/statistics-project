"""Phase 1 - Step 3: Data quality audit, frequency tables, and numeric summaries.

Inputs
------
data/processed/adults_all.csv        adults, examined, not pregnant (n before completeness filters)
data/processed/analytic_sample.csv   final analytic sample

Outputs (reports/phase1/tables/)
--------------------------------
missingness_adults.csv, quality_checks.csv, frequency_tables.csv, numeric_summary.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

from common import add_categories

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
TABLES_DIR = PROJECT_ROOT / "reports" / "phase1" / "tables"

KEY_VARIABLES = {
    "LBXGH": "HbA1c (%)",
    "BMXBMI": "BMI (kg/m^2)",
    "sleep_hours": "Weekly average sleep (h/day)",
    "mvpa_min_week": "Leisure-time MVPA (min/week)",
    "sedentary_hours": "Sedentary time (h/day)",
    "INDFMPIR": "Income-to-poverty ratio",
    "DMDEDUC2": "Education level",
    "DIQ010": "Diagnosed diabetes",
}

NUMERIC_VARIABLES = [
    "RIDAGEYR", "LBXGH", "BMXBMI", "sleep_hours",
    "mod_min_week", "vig_min_week", "mvpa_min_week", "sedentary_hours", "INDFMPIR",
]
CATEGORICAL_VARIABLES = [
    "sex", "age_group", "race_eth", "education", "diabetes_dx", "bmi_cat", "sleep_cat",
]


def missingness_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col, label in KEY_VARIABLES.items():
        n_missing = int(df[col].isna().sum())
        rows.append(
            {"variable": col, "description": label, "n_total": len(df),
             "n_missing": n_missing, "pct_missing": round(100 * n_missing / len(df), 2)}
        )
    return pd.DataFrame(rows)


def quality_checks(adults: pd.DataFrame, sample: pd.DataFrame) -> pd.DataFrame:
    """Range, plausibility, duplicate and logical-consistency checks."""
    checks = [
        ("Duplicate SEQN in adult file", int(adults["SEQN"].duplicated().sum())),
        ("HbA1c outside 3-18 % (analytic sample)",
         int(((sample["LBXGH"] < 3) | (sample["LBXGH"] > 18)).sum())),
        ("BMI outside 10-80 kg/m^2 (analytic sample)",
         int(((sample["BMXBMI"] < 10) | (sample["BMXBMI"] > 80)).sum())),
        ("Sleep < 3 h or > 12 h per day (analytic sample)",
         int(((sample["sleep_hours"] < 3) | (sample["sleep_hours"] > 12)).sum())),
        ("Sedentary time = 0 min (analytic sample)", int((sample["PAD680"] == 0).sum())),
        ("Sedentary time >= 18 h (CAPI soft-edit threshold)",
         int((sample["sedentary_hours"] >= 18).sum())),
        ("MVPA > 2520 min/week (avg > 6 h/day)", int((sample["mvpa_min_week"] > 2520).sum())),
        ("MVPA > 10080 min/week (impossible, > 24 h/day)",
         int((sample["mvpa_min_week"] > 10080).sum())),
        ("Moderate frequency > 0 but unit missing (adults)",
         int(((adults["PAD790Q"] > 0) & adults["PAD790U"].isna()).sum())),
        ("Vigorous frequency > 0 but unit missing (adults)",
         int(((adults["PAD810Q"] > 0) & adults["PAD810U"].isna()).sum())),
        ("Moderate frequency = 0 but minutes reported (adults)",
         int(((adults["PAD790Q"] == 0) & adults["PAD800"].notna()).sum())),
    ]
    return pd.DataFrame(checks, columns=["check", "n_flagged"])


def frequency_tables(df: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for col in CATEGORICAL_VARIABLES:
        counts = df[col].value_counts(dropna=False, sort=False)
        table = counts.rename_axis("category").reset_index(name="n")
        table["percent"] = (100 * table["n"] / len(df)).round(1)
        table.insert(0, "variable", col)
        table["category"] = table["category"].astype(str)
        parts.append(table)
    return pd.concat(parts, ignore_index=True)


def numeric_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in NUMERIC_VARIABLES:
        s = df[col].dropna()
        q1, med, q3 = s.quantile([0.25, 0.5, 0.75])
        rows.append(
            {"variable": col, "n": len(s), "mean": s.mean(), "sd": s.std(),
             "min": s.min(), "q1": q1, "median": med, "q3": q3, "max": s.max(),
             "iqr": q3 - q1, "range": s.max() - s.min(), "skewness": s.skew()}
        )
    return pd.DataFrame(rows).round(2)


def main() -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    adults = pd.read_csv(PROCESSED_DIR / "adults_all.csv")
    sample = add_categories(pd.read_csv(PROCESSED_DIR / "analytic_sample.csv"))

    miss = missingness_table(adults)
    checks = quality_checks(adults, sample)
    freq = frequency_tables(sample)
    numeric = numeric_summary(sample)

    miss.to_csv(TABLES_DIR / "missingness_adults.csv", index=False)
    checks.to_csv(TABLES_DIR / "quality_checks.csv", index=False)
    freq.to_csv(TABLES_DIR / "frequency_tables.csv", index=False)
    numeric.to_csv(TABLES_DIR / "numeric_summary.csv", index=False)

    pd.set_option("display.width", 200)
    print(f"Missingness among {len(adults)} adults (examined, not pregnant):")
    print(miss.to_string(index=False))
    print("\nQuality checks:")
    print(checks.to_string(index=False))
    print(f"\nFrequency tables (analytic sample, n = {len(sample)}):")
    print(freq.to_string(index=False))
    print("\nNumeric summary (unweighted):")
    print(numeric.to_string(index=False))


if __name__ == "__main__":
    main()
