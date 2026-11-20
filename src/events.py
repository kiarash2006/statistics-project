"""Event definitions and probability helpers used in Phase 2."""

import pandas as pd

from common import add_categories

HIGH_HBA1C_CUTOFF = 6.5  # % ; HbA1c >= 6.5 is in the diabetes range

EVENT_DESCRIPTIONS = {
    "high_hba1c": "HbA1c >= 6.5 % (diabetes-range value)",
    "short_sleep": "Average sleep < 7 hours per day",
    "long_sleep": "Average sleep >= 9 hours per day",
    "inactive": "No leisure-time moderate or vigorous activity (0 min/week)",
    "obesity": "BMI >= 30 kg/m^2",
    "age_60plus": "Age >= 60 years",
    "diabetes_dx": "Self-reported diagnosed diabetes (DIQ010 = 1)",
}


def add_events(df: pd.DataFrame) -> pd.DataFrame:
    """Add the categorical variables from Phase 1 and boolean event indicators."""
    df = add_categories(df)
    df["high_hba1c"] = df["LBXGH"] >= HIGH_HBA1C_CUTOFF
    df["short_sleep"] = df["sleep_hours"] < 7
    df["long_sleep"] = df["sleep_hours"] >= 9
    df["inactive"] = df["mvpa_min_week"] == 0
    df["obesity"] = df["BMXBMI"] >= 30
    df["age_60plus"] = df["RIDAGEYR"] >= 60
    df["diabetes_dx"] = df["DIQ010"] == 1
    return df


def prob(event: pd.Series, w: pd.Series = None) -> float:
    """P(event): empirical proportion, or weighted proportion if weights are given."""
    if w is None:
        return float(event.mean())
    return float((w * event).sum() / w.sum())


def cond_prob(event: pd.Series, given: pd.Series, w: pd.Series = None) -> float:
    """P(event | given) = P(event and given) / P(given), empirical or weighted."""
    if w is None:
        return float(event[given].mean())
    return float((w[given] * event[given]).sum() / w[given].sum())