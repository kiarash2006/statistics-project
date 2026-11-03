"""Phase 1 - Step 5: Figures and descriptive group comparisons.

Inputs
------
data/processed/analytic_sample.csv

Outputs
-------
figures/phase1/fig1_hba1c_hist.png ... fig7_age_raw_vs_weighted.png
reports/phase1/tables/group_comparison.csv
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # save figures to files without opening windows
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import add_categories

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
TABLES_DIR = PROJECT_ROOT / "reports" / "phase1" / "tables"
FIG_DIR = PROJECT_ROOT / "figures" / "phase1"

WEIGHT_COL = "WTPH2YR"
COLOR = "#4C72B0"
COLOR_2 = "#DD8452"

plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})


def save(fig, name: str) -> None:
    fig.tight_layout()
    fig.savefig(FIG_DIR / name, dpi=200)
    plt.close(fig)


def histogram(df, col, bins, xlabel, title, name, cutoffs=None):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(df[col], bins=bins, color=COLOR, edgecolor="white")
    ax.axvline(df[col].median(), color="black", linestyle="-", linewidth=1.5,
               label=f"Median = {df[col].median():.1f}")
    for value, label in (cutoffs or {}).items():
        ax.axvline(value, color=COLOR_2, linestyle="--", linewidth=1.2, label=label)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Number of adults")
    ax.set_title(f"{title} (n = {len(df):,})")
    ax.legend(frameon=False)
    save(fig, name)


def boxplot_by_group(df, group_col, value_col, ylabel, title, name):
    categories = list(df[group_col].cat.categories)
    data = [df.loc[df[group_col] == c, value_col].dropna() for c in categories]
    labels = [f"{c}\n(n = {len(d):,})" for c, d in zip(categories, data)]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.boxplot(data, showmeans=True, patch_artist=True,
               boxprops={"facecolor": "#C6D4EA"}, medianprops={"color": "black"},
               meanprops={"marker": "D", "markerfacecolor": COLOR_2, "markeredgecolor": COLOR_2},
               flierprops={"marker": "o", "markersize": 2.5, "alpha": 0.4})
    ax.set_xticks(range(1, len(categories) + 1))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    save(fig, name)


def mvpa_bar_chart(df):
    counts = df["mvpa_cat"].value_counts(sort=False)
    pct = 100 * counts / counts.sum()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(range(len(pct)), pct.to_numpy(), color=COLOR)
    ax.set_xticks(range(len(pct)))
    ax.set_xticklabels(pct.index, fontsize=10)
    for bar, p in zip(bars, pct):
        ax.text(bar.get_x() + bar.get_width() / 2, p + 0.6, f"{p:.1f}%", ha="center")
    ax.set_xlabel("Leisure-time moderate + vigorous activity (minutes per week)")
    ax.set_ylabel("Percent of adults in the sample")
    ax.set_title(f"Weekly leisure-time physical activity (n = {len(df):,})")
    save(fig, "fig4_mvpa_categories.png")


def age_raw_vs_weighted(df):
    raw = 100 * df["age_group"].value_counts(normalize=True, sort=False)
    weighted = 100 * df.groupby("age_group", observed=True)[WEIGHT_COL].sum() / df[WEIGHT_COL].sum()
    x = np.arange(len(raw))
    fig, ax = plt.subplots(figsize=(7, 4.5))
    b1 = ax.bar(x - 0.2, raw.to_numpy(), width=0.4, color=COLOR, label="Unweighted (sample)")
    b2 = ax.bar(x + 0.2, weighted.to_numpy(), width=0.4, color=COLOR_2, label="Weighted (WTPH2YR)")
    for bars in (b1, b2):
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.6,
                    f"{bar.get_height():.1f}", ha="center", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(raw.index)
    ax.set_xlabel("Age group (years)")
    ax.set_ylabel("Percent of adults")
    ax.set_title("Age distribution: sample vs. weighted population")
    ax.legend(frameon=False)
    save(fig, "fig7_age_raw_vs_weighted.png")


def weighted_mean(x, w):
    return float(np.average(x, weights=w))


def group_comparison(df):
    rows = []
    for group_col in ["sleep_cat", "mvpa_cat", "bmi_cat"]:
        for outcome in ["LBXGH", "BMXBMI"]:
            if group_col == "bmi_cat" and outcome == "BMXBMI":
                continue  # BMI categories are defined from BMI itself
            for category, g in df.groupby(group_col, observed=True):
                x = g[outcome]
                q1, med, q3 = x.quantile([0.25, 0.5, 0.75])
                rows.append(
                    {
                        "group_variable": group_col, "group": category, "outcome": outcome,
                        "n": len(x), "mean": x.mean(), "sd": x.std(),
                        "q1": q1, "median": med, "q3": q3,
                        "weighted_mean": weighted_mean(x, g[WEIGHT_COL]),
                    }
                )
    return pd.DataFrame(rows).round(2)


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    df = add_categories(pd.read_csv(PROCESSED_DIR / "analytic_sample.csv"))

    histogram(df, "LBXGH", np.arange(3, 18.01, 0.25), "HbA1c (%)",
              "Distribution of HbA1c among U.S. adults", "fig1_hba1c_hist.png",
              cutoffs={5.7: "5.7% (prediabetes threshold)", 6.5: "6.5% (diabetes threshold)"})
    histogram(df, "BMXBMI", np.arange(10, 80.1, 1.5), "Body mass index (kg/m$^2$)",
              "Distribution of BMI among U.S. adults", "fig2_bmi_hist.png",
              cutoffs={25: "BMI 25", 30: "BMI 30"})
    histogram(df, "sleep_hours", np.arange(2, 14.01, 0.5), "Average sleep duration (hours per day)",
              "Distribution of weekly average sleep duration", "fig3_sleep_hist.png",
              cutoffs={7: "7 h", 9: "9 h"})
    mvpa_bar_chart(df)
    boxplot_by_group(df, "sleep_cat", "LBXGH", "HbA1c (%)",
                     "HbA1c by sleep duration category", "fig5_hba1c_by_sleep.png")
    boxplot_by_group(df, "bmi_cat", "LBXGH", "HbA1c (%)",
                     "HbA1c by BMI category", "fig6_hba1c_by_bmi.png")
    age_raw_vs_weighted(df)

    comparison = group_comparison(df)
    comparison.to_csv(TABLES_DIR / "group_comparison.csv", index=False)
    pd.set_option("display.width", 200)
    print(comparison.to_string(index=False))
    print(f"\nSaved 7 figures to {FIG_DIR}")


if __name__ == "__main__":
    main()