"""Phase 1 - Step 2: Clean special codes, derive analysis variables, and define
the analytic population.

Inputs
------
data/processed/nhanes_merged.csv

Outputs
-------
data/processed/adults_all.csv            adults, examined, not pregnant (before completeness filters)
data/processed/analytic_sample.csv       final analytic sample (complete on all key variables)
reports/phase1/tables/special_code_recoding.csv   special codes set to missing
reports/phase1/tables/sample_flow.csv             participants removed at each step
"""

from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
TABLES_DIR = PROJECT_ROOT / "reports" / "phase1" / "tables"

KEEP_COLUMNS = [
    "SEQN", "RIAGENDR", "RIDAGEYR", "RIDRETH3", "DMDEDUC2", "INDFMPIR",
    "RIDSTATR", "RIDEXPRG", "WTMEC2YR", "WTPH2YR", "SDMVSTRA", "SDMVPSU",
    "LBXGH", "BMXBMI", "SLD012", "SLD013",
    "PAD790Q", "PAD790U", "PAD800", "PAD810Q", "PAD810U", "PAD820", "PAD680",
    "DIQ010", "DIQ050", "DIQ070",
]

# NHANES codes meaning "Refused" (7777) and "Don't know" (9999).
SPECIAL_CODES = {
    "PAD790Q": [7777, 9999],
    "PAD800": [7777, 9999],
    "PAD810Q": [7777, 9999],
    "PAD820": [7777, 9999],
    "PAD680": [7777, 9999],
    "DIQ010": [7, 9],
    "DMDEDUC2": [7, 9],
}

# Conversion of the reported frequency unit to occasions per week.
OCCASIONS_PER_WEEK = {"D": 7.0, "W": 1.0, "M": 12.0 / 52.0, "Y": 1.0 / 52.0}


def recode_special_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Set refused / don't-know codes to missing and log how many were changed."""
    log = []
    for col, codes in SPECIAL_CODES.items():
        mask = df[col].isin(codes)
        log.append({"variable": col, "codes": str(codes), "n_set_to_missing": int(mask.sum())})
        df.loc[mask, col] = np.nan
    return pd.DataFrame(log)


def fix_zero_values(df: pd.DataFrame) -> None:
    """Zeros are stored by SAS as a tiny positive number (~5e-79).
    Convert them to exactly 0 so that 'none' is not mistaken for a real value.
    This affects the activity frequencies (0 = no activity) and sedentary minutes."""
    for col in ["PAD790Q", "PAD810Q", "PAD680"]:
        df[col] = np.where(df[col] < 1e-6, 0.0, df[col])


def weekly_minutes(freq: pd.Series, unit: pd.Series, minutes: pd.Series) -> pd.Series:
    """Minutes of activity per week = frequency x occasions-per-week x minutes per occasion.
    A reported frequency of 0 means no activity, hence 0 minutes."""
    per_week = unit.map(OCCASIONS_PER_WEEK)
    out = freq * per_week * minutes
    return out.where(freq != 0, 0.0)


def derive_variables(df: pd.DataFrame) -> pd.DataFrame:
    df["mod_min_week"] = weekly_minutes(df["PAD790Q"], df["PAD790U"], df["PAD800"])
    df["vig_min_week"] = weekly_minutes(df["PAD810Q"], df["PAD810U"], df["PAD820"])
    # Total leisure-time moderate + vigorous minutes; missing if either part is missing.
    df["mvpa_min_week"] = df["mod_min_week"] + df["vig_min_week"]
    df["sedentary_hours"] = df["PAD680"] / 60.0
    # Weekly average sleep: 5 workdays + 2 non-workdays.
    df["sleep_hours"] = (5.0 * df["SLD012"] + 2.0 * df["SLD013"]) / 7.0
    return df


def main() -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(PROCESSED_DIR / "nhanes_merged.csv")[KEEP_COLUMNS]

    recoding_log = recode_special_codes(df)
    fix_zero_values(df)
    df = derive_variables(df)
    recoding_log.to_csv(TABLES_DIR / "special_code_recoding.csv", index=False)
    print("Special codes set to missing:")
    print(recoding_log.to_string(index=False))

    # Sequential inclusion criteria (each step is applied to the output of the previous one).
    steps = [
        ("All NHANES 2021-2023 participants (DEMO_L)", lambda d: d),
        ("Age >= 20 years", lambda d: d[d["RIDAGEYR"] >= 20]),
        ("Examined in the MEC (RIDSTATR == 2)", lambda d: d[d["RIDSTATR"] == 2]),
        ("Not pregnant (RIDEXPRG != 1)", lambda d: d[d["RIDEXPRG"] != 1]),
        ("HbA1c available with phlebotomy weight > 0",
         lambda d: d[d["LBXGH"].notna() & (d["WTPH2YR"] > 0)]),
        ("BMI available", lambda d: d[d["BMXBMI"].notna()]),
        ("Weekly sleep duration available", lambda d: d[d["sleep_hours"].notna()]),
        ("Leisure-time MVPA available", lambda d: d[d["mvpa_min_week"].notna()]),
        ("Sedentary time available", lambda d: d[d["sedentary_hours"].notna()]),
    ]

    flow_rows = []
    current = df
    adults_all = None
    for label, rule in steps:
        before = len(current)
        current = rule(current)
        flow_rows.append(
            {"step": label, "n_remaining": len(current), "n_removed": before - len(current)}
        )
        if label.startswith("Not pregnant"):
            adults_all = current.copy()

    flow = pd.DataFrame(flow_rows)
    flow.loc[0, "n_removed"] = 0
    print("\nSample flow:")
    print(flow.to_string(index=False))

    adults_all.to_csv(PROCESSED_DIR / "adults_all.csv", index=False)
    current.to_csv(PROCESSED_DIR / "analytic_sample.csv", index=False)
    flow.to_csv(TABLES_DIR / "sample_flow.csv", index=False)

    print("\nDerived variables in the analytic sample:")
    print(
        current[["mod_min_week", "vig_min_week", "mvpa_min_week", "sedentary_hours", "sleep_hours"]]
        .describe().round(2).to_string()
    )
    print("\nMVPA > 10080 min/week (24 h/day):", int((current["mvpa_min_week"] > 10080).sum()))


if __name__ == "__main__":
    main()