"""Phase 2 - Step 1: Events, joint and conditional probabilities, independence, Bayes,
subgroup probabilities, and the role of sampling weights (tasks 1-4, 9, A.1, A.4).

Input : data/processed/analytic_sample.csv
Output: reports/phase2/tables/*.csv and figures/phase2/p2_fig1*.png, p2_fig2*.png
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from events import EVENT_DESCRIPTIONS, add_events, cond_prob, prob

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
TABLES_DIR = PROJECT_ROOT / "reports" / "phase2" / "tables"
FIG_DIR = PROJECT_ROOT / "figures" / "phase2"
W = "WTPH2YR"
COLOR, COLOR_2 = "#4C72B0", "#DD8452"

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def events_table(df):
    w = df[W]
    rows = []
    for name, text in EVENT_DESCRIPTIONS.items():
        rows.append({"event": name, "definition": text, "n_events": int(df[name].sum()),
                     "p_unweighted": prob(df[name]), "p_weighted": prob(df[name], w)})
    return pd.DataFrame(rows)


def joint_table(df, a="short_sleep", b="high_hba1c"):
    """2 x 2 table of two events with empirical joint probabilities and the
    joint probabilities expected under independence, P(A) x P(B)."""
    pa, pb = prob(df[a]), prob(df[b])
    cells = [
        ("A and B", df[a] & df[b], pa * pb),
        ("A and not B", df[a] & ~df[b], pa * (1 - pb)),
        ("not A and B", ~df[a] & df[b], (1 - pa) * pb),
        ("not A and not B", ~df[a] & ~df[b], (1 - pa) * (1 - pb)),
    ]
    rows = [{"cell": name, "n": int(mask.sum()), "joint_probability": prob(mask),
             "expected_if_independent": exp} for name, mask, exp in cells]
    rows += [{"cell": "P(A) marginal", "n": int(df[a].sum()), "joint_probability": pa, "expected_if_independent": None},
             {"cell": "P(B) marginal", "n": int(df[b].sum()), "joint_probability": pb, "expected_if_independent": None}]
    return pd.DataFrame(rows)


def conditional_table(df):
    w = df[W]
    b = df["high_hba1c"]
    conditions = [
        ("short sleep (<7 h)", df["short_sleep"]),
        ("recommended sleep (7 to <9 h)", ~df["short_sleep"] & ~df["long_sleep"]),
        ("long sleep (>=9 h)", df["long_sleep"]),
        ("no leisure-time activity", df["inactive"]),
        ("some leisure-time activity", ~df["inactive"]),
        ("obesity (BMI >= 30)", df["obesity"]),
        ("no obesity (BMI < 30)", ~df["obesity"]),
        ("age >= 60", df["age_60plus"]),
        ("age < 60", ~df["age_60plus"]),
    ]
    p_b, p_bw = prob(b), prob(b, w)
    rows = []
    for label, given in conditions:
        pc, pcw = cond_prob(b, given), cond_prob(b, given, w)
        rows.append({"given": label, "n": int(given.sum()),
                     "p_b_given_unweighted": pc, "ratio_to_overall": pc / p_b,
                     "p_b_given_weighted": pcw, "ratio_to_overall_weighted": pcw / p_bw})
    return pd.DataFrame(rows)


def independence_table(df):
    b = df["high_hba1c"]
    pb = prob(b)
    rows = []
    for name in ["short_sleep", "long_sleep", "inactive", "obesity", "age_60plus"]:
        a = df[name]
        joint, expected = prob(a & b), prob(a) * pb
        rows.append({"event_A": name, "P(A and B)": joint, "P(A) x P(B)": expected,
                     "joint / expected": joint / expected, "P(B|A)": cond_prob(b, a), "P(B)": pb,
                     "P(B|A) - P(B)": cond_prob(b, a) - pb})
    return pd.DataFrame(rows)


def short_sleep_by_age(df):
    rows = []
    for g, sub in df.groupby("age_group", observed=True):
        b, a = sub["high_hba1c"], sub["short_sleep"]
        rows.append({"age_group": g, "n": len(sub), "P(short sleep)": prob(a),
                     "P(B | short sleep)": cond_prob(b, a), "P(B | not short sleep)": cond_prob(b, ~a)})
    return pd.DataFrame(rows)

def bayes_table(df):
    """Bayes' theorem for P(diagnosed diabetes | HbA1c >= 6.5).
    Participants with borderline diabetes (DIQ010 = 3) are excluded from this calculation."""
    sub = df[df["DIQ010"].isin([1, 2])]
    out = []
    for label, w in (("unweighted", None), ("weighted", sub[W])):
        d, b = sub["diabetes_dx"], sub["high_hba1c"]
        prior = prob(d, w)
        sens = cond_prob(b, d, w)            # P(B | D)
        fpr = cond_prob(b, ~d, w)            # P(B | not D)
        evidence = sens * prior + fpr * (1 - prior)
        posterior = sens * prior / evidence  # Bayes
        direct = cond_prob(d, b, w)          # P(D | B) computed directly
        out.append({"version": label, "n": len(sub), "P(D) prior": prior, "P(B|D)": sens,
                    "P(B|not D)": fpr, "P(B) total probability": evidence,
                    "P(D|B) by Bayes": posterior, "P(D|B) direct": direct,
                    "P(not D|B), i.e. high HbA1c without diagnosis": 1 - posterior})
    return pd.DataFrame(out)


def subgroup_table(df):
    b = df["high_hba1c"]
    overall = prob(b)
    rows = []
    for col in ["sex", "age_group", "race_eth", "bmi_cat", "sleep_cat", "mvpa_cat"]:
        for cat, idx in df.groupby(col, observed=True).groups.items():
            sub = df.loc[idx]
            rows.append({"variable": col, "group": cat, "n": len(sub), "n_events": int(sub["high_hba1c"].sum()),
                         "p_unweighted": prob(sub["high_hba1c"]), "p_weighted": prob(sub["high_hba1c"], sub[W]),
                         "diff_from_overall_pp": 100 * (prob(sub["high_hba1c"]) - overall)})
    return pd.DataFrame(rows)


def weights_effect_table(df):
    w, b = df[W], df["high_hba1c"]
    rows = [{"quantity": "P(B) overall", "unweighted": prob(b), "weighted": prob(b, w)}]
    for cat, sub in df.groupby("age_group", observed=True):
        rows.append({"quantity": f"P(B | age {cat})", "unweighted": prob(sub["high_hba1c"]),
                     "weighted": prob(sub["high_hba1c"], sub[W])})
    rows.append({"quantity": "P(B | short sleep)", "unweighted": cond_prob(b, df["short_sleep"]),
                 "weighted": cond_prob(b, df["short_sleep"], w)})
    rows.append({"quantity": "P(short sleep)", "unweighted": prob(df["short_sleep"]),
                 "weighted": prob(df["short_sleep"], w)})
    # Direct standardization: unweighted age-specific probabilities combined with the
    # weighted (population) age distribution.
    age_share = df.groupby("age_group", observed=True)[W].sum() / w.sum()
    age_p = df.groupby("age_group", observed=True)["high_hba1c"].mean()
    rows.append({"quantity": "P(B) standardized to the weighted age distribution",
                 "unweighted": float((age_share * age_p).sum()), "weighted": prob(b, w)})
    return pd.DataFrame(rows)


def figure_conditional(df):
    overall = prob(df["high_hba1c"])
    panels = [("sleep_cat", "Sleep category"), ("mvpa_cat", "Leisure-time activity (min/week)"),
              ("bmi_cat", "BMI category"), ("age_group", "Age group (years)")]
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    for ax, (col, title) in zip(axes.ravel(), panels):
        g = df.groupby(col, observed=True)["high_hba1c"]
        p, n = g.mean() * 100, g.size()
        bars = ax.bar(range(len(p)), p.to_numpy(), color=COLOR)
        ax.axhline(overall * 100, color="black", linestyle="--", linewidth=1, label=f"Overall = {overall * 100:.1f}%")
        for bar, val in zip(bars, p):
            ax.text(bar.get_x() + bar.get_width() / 2, val + 0.4, f"{val:.1f}", ha="center", fontsize=9)
        ax.set_xticks(range(len(p)))
        ax.set_xticklabels([f"{str(c).replace(' (', chr(10) + '(')}\n(n = {n[c]:,})" for c in p.index], fontsize=7.5)
        ax.set_title(title)
        ax.set_ylabel("P(HbA1c >= 6.5%) (%)")
        ax.legend(frameon=False, fontsize=8)
    fig.suptitle("Conditional probability of a diabetes-range HbA1c by group (unweighted)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "p2_fig1_conditional_probabilities.png", dpi=200)
    plt.close(fig)

def figure_weights(table):
    keep = table[~table["quantity"].str.contains("standardized|P\\(short sleep\\)")].copy()
    x = range(len(keep))
    fig, ax = plt.subplots(figsize=(9, 4.5))
    b1 = ax.bar([i - 0.2 for i in x], keep["unweighted"] * 100, width=0.4, color=COLOR, label="Unweighted (sample)")
    b2 = ax.bar([i + 0.2 for i in x], keep["weighted"] * 100, width=0.4, color=COLOR_2, label="Weighted (WTPH2YR)")
    for bars in (b1, b2):
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3, f"{bar.get_height():.1f}",
                    ha="center", fontsize=8.5)
    ax.set_xticks(list(x))
    ax.set_xticklabels(keep["quantity"], rotation=15, ha="right", fontsize=9)
    ax.set_ylabel("Probability (%)")
    ax.set_title("Empirical probability of HbA1c >= 6.5%: unweighted vs. weighted")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "p2_fig2_weighted_vs_unweighted.png", dpi=200)
    plt.close(fig)


def main():
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    df = add_events(pd.read_csv(PROCESSED_DIR / "analytic_sample.csv"))

    tables = {
        "events_definition": events_table(df),
        "joint_short_sleep_high_hba1c": joint_table(df),
        "conditional_probabilities": conditional_table(df),
        "independence_check": independence_table(df),
        "short_sleep_by_age": short_sleep_by_age(df),
        "bayes_diabetes": bayes_table(df),
        "subgroup_probabilities": subgroup_table(df),
        "weights_effect_probabilities": weights_effect_table(df),
    }
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)
    for name, table in tables.items():
        table.round(4).to_csv(TABLES_DIR / f"{name}.csv", index=False)
        print(f"\n=== {name} ===")
        print(table.round(4).to_string(index=False))

    figure_conditional(df)
    figure_weights(tables["weights_effect_probabilities"])
    print(f"\nSaved 2 figures to {FIG_DIR}")


if __name__ == "__main__":
    main()