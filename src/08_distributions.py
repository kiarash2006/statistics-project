"""Phase 2 - Step 2: Binomial model, normal approximation, expectation and variance,
and covariance (tasks 5-8, A.2, A.3).

Input : data/processed/analytic_sample.csv
Output: reports/phase2/tables/*.csv and figures/phase2/p2_fig3*.png ... p2_fig7*.png
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from events import add_events, prob

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
TABLES_DIR = PROJECT_ROOT / "reports" / "phase2" / "tables"
FIG_DIR = PROJECT_ROOT / "figures" / "phase2"
W = "WTPH2YR"
COLOR, COLOR_2 = "#4C72B0", "#DD8452"
SEED = 2026
N_SUB = 90          # size of each equal-sized subsample (the smallest design cluster has 94 adults)
N_RANDOM = 10_000   # number of random subsamples
N_REPS = 1_000      # repetitions of the cluster-based subsampling

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


# ------------------------------------------------------------------ binomial model (task 5, A.2)
def binomial_analysis(df):
    rng = np.random.default_rng(SEED)
    b = df["high_hba1c"].to_numpy()
    n_total, p_hat = len(b), b.mean()
    k_total = int(b.sum())

    # Scenario 1: simple random subsamples of the analytic sample.
    counts = np.array([b[rng.choice(n_total, N_SUB, replace=False)].sum() for _ in range(N_RANDOM)])
    ks = np.arange(0, N_SUB + 1)
    emp_pmf = np.bincount(counts, minlength=N_SUB + 1) / N_RANDOM
    pmf_table = pd.DataFrame({
        "k": ks,
        "empirical": emp_pmf,
        "binomial": stats.binom.pmf(ks, N_SUB, p_hat),
        "hypergeometric": stats.hypergeom.pmf(ks, n_total, k_total, N_SUB),
    })
    binom_var = N_SUB * p_hat * (1 - p_hat)
    hyper_var = binom_var * (n_total - N_SUB) / (n_total - 1)

    # Scenario 2: equal-sized random subsamples drawn within each design cluster
    # (masked stratum x PSU). If clusters differ in their probability, the counts vary more
    # than a binomial model allows (over-dispersion).
    clusters = [g["high_hba1c"].to_numpy() for _, g in df.groupby(["SDMVSTRA", "SDMVPSU"])]
    dispersion = []
    cluster_means = []
    for _ in range(N_REPS):
        cluster_counts = np.array([c[rng.choice(len(c), N_SUB, replace=False)].sum() for c in clusters])
        dispersion.append(cluster_counts.var(ddof=1) / binom_var)
        cluster_means.append(cluster_counts.mean())
    dispersion = np.array(dispersion)

    summary = pd.DataFrame([
        {"scenario": f"Random subsamples of {N_SUB} adults ({N_RANDOM:,} draws)",
         "mean_of_counts": counts.mean(), "variance_of_counts": counts.var(ddof=1),
         "binomial_mean": N_SUB * p_hat, "binomial_variance": binom_var,
         "hypergeometric_variance": hyper_var,
         "variance_ratio_to_binomial": counts.var(ddof=1) / binom_var},
        {"scenario": f"Subsamples of {N_SUB} adults within each of {len(clusters)} design clusters ({N_REPS:,} repetitions)",
         "mean_of_counts": float(np.mean(cluster_means)), "variance_of_counts": float(np.mean(dispersion) * binom_var),
         "binomial_mean": N_SUB * p_hat, "binomial_variance": binom_var,
         "hypergeometric_variance": None,
         "variance_ratio_to_binomial": float(np.mean(dispersion))},
    ])
    cluster_table = (df.groupby(["SDMVSTRA", "SDMVPSU"])["high_hba1c"]
                     .agg(n="size", n_events="sum", p="mean").reset_index())
    extra = {"p_hat": p_hat, "dispersion_q05": float(np.quantile(dispersion, 0.05)),
             "dispersion_q95": float(np.quantile(dispersion, 0.95))}
    return counts, pmf_table, summary, cluster_table, dispersion, extra


def figure_binomial(counts, pmf_table, dispersion, p_hat):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    ax = axes[0]
    sub = pmf_table[pmf_table["k"] <= 26]
    ax.bar(sub["k"], sub["empirical"], color=COLOR, alpha=0.8, label=f"Empirical ({N_RANDOM:,} random subsamples)")
    ax.plot(sub["k"], sub["binomial"], color=COLOR_2, marker="o", markersize=3.5, linewidth=1.5,
            label=f"Binomial(n = {N_SUB}, p = {p_hat:.3f})")
    ax.set_xlabel(f"Number of adults with HbA1c >= 6.5% in a subsample of {N_SUB}")
    ax.set_ylabel("Probability")
    ax.set_title("(a) Random subsamples vs. binomial model")
    ax.set_ylim(0, sub[["empirical", "binomial"]].to_numpy().max() * 1.3)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    ax = axes[1]
    ax.hist(dispersion, bins=30, color=COLOR, edgecolor="white")
    ax.axvline(1, color="black", linestyle="--", label="Binomial (ratio = 1)")
    ax.axvline(dispersion.mean(), color=COLOR_2, linewidth=2, label=f"Mean ratio = {dispersion.mean():.2f}")
    ax.set_xlabel("Variance of cluster counts / binomial variance")
    ax.set_ylabel("Number of repetitions")
    ax.set_title(f"(b) Subsamples of {N_SUB} within each design cluster")
    ax.legend(frameon=False, fontsize=8.5)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "p2_fig3_binomial_vs_empirical.png", dpi=200)
    plt.close(fig)


# ------------------------------------------------------------------ normal approximation (tasks 6, A.3)
def normal_check(x, variable, scale):
    mu, sd = x.mean(), x.std()
    z = (x - mu) / sd
    (_, _), (_, _, r) = stats.probplot(x, dist="norm")
    return {"variable": variable, "scale": scale, "n": len(x), "mean": mu, "sd": sd,
            "skewness": x.skew(), "excess_kurtosis": x.kurt(),
            "pct_within_1sd": 100 * (z.abs() <= 1).mean(), "pct_within_2sd": 100 * (z.abs() <= 2).mean(),
            "pct_within_3sd": 100 * (z.abs() <= 3).mean(), "n_beyond_3sd": int((z.abs() > 3).sum()),
            "qq_correlation": r}


def normal_figure(panels, fname, title):
    """panels: list of (series, xlabel) ; one row per panel with histogram + Q-Q plot."""
    fig, axes = plt.subplots(len(panels), 2, figsize=(10, 3.8 * len(panels)), squeeze=False)
    for row, (x, xlabel) in zip(axes, panels):
        mu, sd = x.mean(), x.std()
        ax = row[0]
        ax.hist(x, bins=45, density=True, color=COLOR, edgecolor="white", alpha=0.85)
        grid = np.linspace(x.min(), x.max(), 300)
        ax.plot(grid, stats.norm.pdf(grid, mu, sd), color=COLOR_2, linewidth=2,
                label=f"Normal(mean = {mu:.2f}, SD = {sd:.2f})")
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Density")
        ax.legend(frameon=False, fontsize=8.5)
        ax = row[1]
        (osm, osr), (slope, intercept, r) = stats.probplot(x, dist="norm")
        ax.scatter(osm, osr, s=4, alpha=0.4, color=COLOR)
        ax.plot(osm, slope * osm + intercept, color=COLOR_2, linewidth=1.8, label=f"Reference line (r = {r:.3f})")
        ax.set_xlabel("Theoretical quantiles (standard normal)")
        ax.set_ylabel(f"Sample quantiles: {xlabel}")
        ax.legend(frameon=False, fontsize=8.5)
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(FIG_DIR / fname, dpi=200)
    plt.close(fig)


def normal_analysis(df):
    rows = [normal_check(df["sleep_hours"], "Sleep (h/day)", "raw"),
            normal_check(df["BMXBMI"], "BMI (kg/m^2)", "raw"),
            normal_check(np.log(df["BMXBMI"]), "BMI (kg/m^2)", "natural log"),
            normal_check(df["LBXGH"], "HbA1c (%)", "raw"),
            normal_check(np.log(df["LBXGH"]), "HbA1c (%)", "natural log")]
    normal_figure([(df["sleep_hours"], "Sleep (hours per day)")], "p2_fig4_normal_sleep.png",
                  "Normal approximation: weekly average sleep")
    normal_figure([(df["BMXBMI"], "BMI (kg/m$^2$)"), (np.log(df["BMXBMI"]), "log(BMI)")],
                  "p2_fig5_normal_bmi.png", "Normal approximation: BMI, raw and log scale")
    normal_figure([(df["LBXGH"], "HbA1c (%)"), (np.log(df["LBXGH"]), "log(HbA1c)")],
                  "p2_fig6_normal_hba1c.png", "Normal approximation: HbA1c, raw and log scale")
    reference = {"variable": "Normal distribution (reference)", "scale": "", "n": None, "mean": None, "sd": None,
                 "skewness": 0.0, "excess_kurtosis": 0.0,
                 "pct_within_1sd": 100 * (stats.norm.cdf(1) - stats.norm.cdf(-1)),
                 "pct_within_2sd": 100 * (stats.norm.cdf(2) - stats.norm.cdf(-2)),
                 "pct_within_3sd": 100 * (stats.norm.cdf(3) - stats.norm.cdf(-3)), "n_beyond_3sd": None,
                 "qq_correlation": 1.0}
    return pd.DataFrame(rows + [reference])

# ------------------------------------------------------------------ expectation and variance (task 7)
def weighted_mean_var(x, w):
    mu = np.average(x, weights=w)
    return mu, np.average((x - mu) ** 2, weights=w)


def expectation_variance(df, p_hat):
    w = df[W]
    rows = []
    ind = df["high_hba1c"].astype(float)
    mu_w, var_w = weighted_mean_var(ind, w)
    rows.append({"random_variable": "I_B = 1 if HbA1c >= 6.5% (Bernoulli)", "unit": "probability",
                 "expectation": ind.mean(), "variance": ind.var(ddof=1), "sd": ind.std(),
                 "expectation_weighted": mu_w, "variance_weighted": var_w})
    rows.append({"random_variable": f"K = number of I_B = 1 in {N_SUB} random adults (Binomial)", "unit": "adults",
                 "expectation": N_SUB * p_hat, "variance": N_SUB * p_hat * (1 - p_hat),
                 "sd": np.sqrt(N_SUB * p_hat * (1 - p_hat)),
                 "expectation_weighted": N_SUB * mu_w, "variance_weighted": N_SUB * mu_w * (1 - mu_w)})
    for col, label, unit in [("LBXGH", "HbA1c", "%"), ("BMXBMI", "BMI", "kg/m^2"), ("sleep_hours", "Sleep", "h/day")]:
        mu_w, var_w = weighted_mean_var(df[col], w)
        rows.append({"random_variable": label, "unit": unit, "expectation": df[col].mean(),
                     "variance": df[col].var(ddof=1), "sd": df[col].std(),
                     "expectation_weighted": mu_w, "variance_weighted": var_w})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ covariance (task 8)
def covariance_analysis(df):
    pairs = [("BMXBMI", "LBXGH", "kg/m^2 x %"), ("sleep_hours", "LBXGH", "h/day x %"),
             ("mvpa_min_week", "LBXGH", "min/week x %"), ("sedentary_hours", "LBXGH", "h/day x %"),
             ("sleep_hours", "BMXBMI", "h/day x kg/m^2"), ("mvpa_min_week", "BMXBMI", "min/week x kg/m^2")]
    rows = []
    for x, y, unit in pairs:
        cov = float(np.cov(df[x], df[y], ddof=1)[0, 1])
        rows.append({"x": x, "y": y, "covariance": cov, "unit": unit,
                     "direction": "positive" if cov > 0 else "negative"})
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.3))
    specs = [("BMXBMI", "LBXGH", "BMI (kg/m$^2$)", "HbA1c (%)", False),
             ("sleep_hours", "LBXGH", "Average sleep (hours per day)", "HbA1c (%)", False),
             ("mvpa_min_week", "LBXGH", "Leisure-time MVPA (min/week, symmetric log axis)", "HbA1c (%)", True)]
    for ax, (x, y, xl, yl, log) in zip(axes, specs):
        ax.scatter(df[x], df[y], s=5, alpha=0.25, color=COLOR)
        ax.set_xlabel(xl, fontsize=9)
        ax.set_ylabel(yl)
        if log:
            ax.set_xscale("symlog", linthresh=10)
        cov = np.cov(df[x], df[y], ddof=1)[0, 1]
        ax.set_title(f"Covariance = {cov:,.2f}")
    fig.suptitle(f"Scatter plots of HbA1c against BMI, sleep, and activity (n = {len(df):,})")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "p2_fig7_scatter_covariance.png", dpi=200)
    plt.close(fig)
    return pd.DataFrame(rows)


def main():
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    df = add_events(pd.read_csv(PROCESSED_DIR / "analytic_sample.csv"))
    p_hat = prob(df["high_hba1c"])

    counts, pmf_table, summary, cluster_table, dispersion, extra = binomial_analysis(df)
    figure_binomial(counts, pmf_table, dispersion, p_hat)
    tables = {
        "binomial_pmf": pmf_table[pmf_table["k"] <= 30],
        "binomial_summary": summary,
        "cluster_proportions": cluster_table,
        "normal_approximation": normal_analysis(df),
        "expectation_variance": expectation_variance(df, p_hat),
        "covariance_pairs": covariance_analysis(df),
    }
    pd.set_option("display.width", 230)
    pd.set_option("display.max_columns", 30)
    for name, table in tables.items():
        table.round(4).to_csv(TABLES_DIR / f"{name}.csv", index=False)
        print(f"\n=== {name} ===")
        print(table.round(4).to_string(index=False))
    print(f"\np_hat = {extra['p_hat']:.4f}; 90% range of the cluster dispersion ratio: "
          f"{extra['dispersion_q05']:.2f} to {extra['dispersion_q95']:.2f}")
    print(f"Saved 5 figures to {FIG_DIR}")


if __name__ == "__main__":
    main()