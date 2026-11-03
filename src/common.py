"""Shared helpers: value labels and derived categorical variables."""

import numpy as np
import pandas as pd

SEX_LABELS = {1: "Male", 2: "Female"}
RACE_LABELS = {
    1: "Mexican American",
    2: "Other Hispanic",
    3: "Non-Hispanic White",
    4: "Non-Hispanic Black",
    6: "Non-Hispanic Asian",
    7: "Other / multiracial",
}
EDUC_LABELS = {
    1: "Less than 9th grade",
    2: "9th-11th grade",
    3: "High school graduate / GED",
    4: "Some college / associate degree",
    5: "College graduate or above",
}
DIABETES_LABELS = {1: "Yes", 2: "No", 3: "Borderline"}


def add_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Add labelled categorical versions of the main variables."""
    df = df.copy()
    df["sex"] = df["RIAGENDR"].map(SEX_LABELS)
    df["race_eth"] = df["RIDRETH3"].map(RACE_LABELS)
    df["education"] = df["DMDEDUC2"].map(EDUC_LABELS)
    df["diabetes_dx"] = df["DIQ010"].map(DIABETES_LABELS)

    df["age_group"] = pd.cut(
        df["RIDAGEYR"], bins=[20, 40, 60, np.inf], right=False,
        labels=["20-39", "40-59", "60+"],
    )
    df["bmi_cat"] = pd.cut(
        df["BMXBMI"], bins=[0, 18.5, 25, 30, np.inf], right=False,
        labels=["Underweight (<18.5)", "Normal (18.5-24.9)",
                "Overweight (25.0-29.9)", "Obesity (>=30)"],
    )
    df["sleep_cat"] = pd.cut(
        df["sleep_hours"], bins=[0, 7, 9, np.inf], right=False,
        labels=["Short (<7 h)", "Recommended (7 to <9 h)", "Long (>=9 h)"],
    )
    df["mvpa_cat"] = pd.Categorical(
        np.select(
            [df["mvpa_min_week"].isna(), df["mvpa_min_week"] == 0,
             df["mvpa_min_week"] < 150, df["mvpa_min_week"] < 300],
            [None, "None (0 min)", "Some (<150 min)", "150 to <300 min"],
            default="300+ min",
        ),
        categories=["None (0 min)", "Some (<150 min)", "150 to <300 min", "300+ min"],
        ordered=True,
    )
    return df