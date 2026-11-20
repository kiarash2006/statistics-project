"""Phase 2 - Step 3: Build the Phase 2 report (PDF) from the saved tables and figures.

Inputs
------
reports/phase2/tables/*.csv and figures/phase2/*.png (created by scripts 07 and 08)

Output
------
reports/phase2/phase2_report.pdf
"""

from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TABLES_DIR = PROJECT_ROOT / "reports" / "phase2" / "tables"
FIG_DIR = PROJECT_ROOT / "figures" / "phase2"
OUT_PATH = PROJECT_ROOT / "reports" / "phase2" / "phase2_report.pdf"

AUTHOR_LINE = "[Kiarash Hajizadeh 403170128]"

base = getSampleStyleSheet()
STY = {
    "title": ParagraphStyle("title", parent=base["Title"], fontSize=17, leading=21, spaceAfter=6),
    "subtitle": ParagraphStyle("subtitle", parent=base["Normal"], fontSize=11, leading=14, alignment=1,
                               textColor=colors.HexColor("#444444")),
    "h1": ParagraphStyle("h1", parent=base["Heading1"], fontSize=13.5, leading=17, spaceBefore=12, spaceAfter=5),
    "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=11, leading=14, spaceBefore=8, spaceAfter=3),
    "body": ParagraphStyle("body", parent=base["Normal"], fontSize=10, leading=13.5, alignment=TA_JUSTIFY,
                           spaceAfter=6),
    "caption": ParagraphStyle("caption", parent=base["Normal"], fontSize=8.5, leading=11,
                              textColor=colors.HexColor("#333333"), spaceBefore=2, spaceAfter=8),
    "cell": ParagraphStyle("cell", parent=base["Normal"], fontSize=7.8, leading=9.5),
    "cellb": ParagraphStyle("cellb", parent=base["Normal"], fontSize=7.8, leading=9.5, fontName="Helvetica-Bold"),
}
_counter = {"table": 0, "figure": 0}


def P(text, style="body"):
    return Paragraph(text, STY[style])


def E(text):
    return escape(str(text))


def make_table(rows, header, widths, caption):
    _counter["table"] += 1
    data = [[Paragraph(E(h), STY["cellb"]) for h in header]]
    for r in rows:
        data.append([Paragraph(E(c), STY["cell"]) for c in r])
    t = Table(data, colWidths=[w * inch for w in widths], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E6ECF5")),
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.black),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F7F7")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    cap = Paragraph(f"<b>Table {_counter['table']}.</b> {caption}", STY["caption"])
    items = [Spacer(1, 4), t, cap]
    return [KeepTogether(items)] if len(rows) <= 14 else items


def figure(filename, caption, width=5.2):
    _counter["figure"] += 1
    path = FIG_DIR / filename
    iw, ih = ImageReader(str(path)).getSize()
    img = Image(str(path), width=width * inch, height=width * inch * ih / iw)
    return KeepTogether([img, Paragraph(f"<b>Figure {_counter['figure']}.</b> {caption}", STY["caption"])])


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(0.85 * inch, 0.55 * inch, "Phase 2 Report - NHANES 2021-2023: Probability and Distributions")
    canvas.drawRightString(letter[0] - 0.85 * inch, 0.55 * inch, f"Page {doc.page}")
    canvas.restoreState()


def pc(x, d=1):
    return f"{100 * x:.{d}f}%"


EVENT_LABELS = {
    "high_hba1c": "B: high HbA1c", "short_sleep": "A: short sleep", "long_sleep": "Long sleep",
    "inactive": "Inactive", "obesity": "Obesity", "age_60plus": "Age 60+", "diabetes_dx": "D: diagnosed diabetes",
}


def load():
    return {p.stem: pd.read_csv(p) for p in TABLES_DIR.glob("*.csv")}


def build_story(t):
    ev = t["events_definition"].set_index("event")
    joint = t["joint_short_sleep_high_hba1c"].set_index("cell")
    cond = t["conditional_probabilities"].set_index("given")
    ind = t["independence_check"].set_index("event_A")
    ssa = t["short_sleep_by_age"]
    bs = t["binomial_summary"]
    cl = t["cluster_proportions"]
    na = t["normal_approximation"]
    evv = t["expectation_variance"]
    cov = t["covariance_pairs"]
    bayes = t["bayes_diabetes"].set_index("version")
    sg = t["subgroup_probabilities"]
    we = t["weights_effect_probabilities"].set_index("quantity")
    n = int(ssa["n"].sum())
    pB, pBw = ev.loc["high_hba1c", "p_unweighted"], ev.loc["high_hba1c", "p_weighted"]
    pA = ev.loc["short_sleep", "p_unweighted"]
    nB = int(ev.loc["high_hba1c", "n_events"])
    disp = bs.iloc[1]["variance_ratio_to_binomial"]

    S = []
    S += [Spacer(1, 6),
          P("Sleep Duration, Physical Activity, and Glycated Hemoglobin Among U.S. Adults", "title"),
          P("Analysis of NHANES August 2021 - August 2023", "subtitle"),
          P("<b>Phase 2 Report: Probability and Probability Distributions</b>", "subtitle"), Spacer(1, 4),
          P(f"{E(AUTHOR_LINE)} &nbsp;|&nbsp; Statistics Course Project, Fall 1405 &nbsp;|&nbsp; Track A (NHANES)",
            "subtitle"),
          Spacer(1, 10)]

    S += [P("Summary", "h1"),
          P(f"This report translates the Phase 1 data ({n:,} adults) into the language of probability. We define events "
            f"related to the project question, compute marginal, joint, and conditional probabilities, examine independence, "
            f"apply Bayes' theorem, and examine when binomial and normal models are reasonable. The probability of a "
            f"diabetes-range HbA1c (>= 6.5%) is {pc(pB)} in the sample and {pc(pBw)} in the weighted population; it is "
            f"{pc(cond.loc['no leisure-time activity', 'p_b_given_unweighted'])} among adults with no leisure-time activity and "
            f"{pc(cond.loc['recommended sleep (7 to <9 h)', 'p_b_given_unweighted'])} among adults with recommended sleep. "
            f"Short sleep is roughly consistent with independence from a high HbA1c, whereas obesity, inactivity, long sleep, "
            f"and age are not. A binomial model describes counts in random subsamples well (variance ratio "
            f"{bs.iloc[0]['variance_ratio_to_binomial']:.2f}) but fails for subsamples taken within the survey's design clusters "
            f"(ratio {disp:.2f}). BMI is approximately normal on the log scale, whereas HbA1c remains strongly skewed. "
            f"All results are descriptive; formal inference begins in Phase 3.")]

    # -------------------------------------------------------------- 1
    ev_rows = [[EVENT_LABELS[e], r.definition, f"{int(r.n_events):,}", pc(r.p_unweighted), pc(r.p_weighted)]
               for e, r in ev.iterrows()]
    S += [P("1. Events and Random Variables", "h1"),
          P("We work with the analytic sample of Phase 1 (adults aged 20 or older, examined, not pregnant, with complete data). "
            "Probabilities are empirical relative frequencies in this sample; a weighted version uses the phlebotomy weight "
            "WTPH2YR. Each event corresponds to a precise observation in the data (Table 1). The outcome event <b>B</b> is a "
            "diabetes-range HbA1c, defined by LBXGH >= 6.5%, the cutoff commonly used for the laboratory diagnosis of diabetes. "
            "The exposure event <b>A</b> is short sleep, defined by weekly average sleep below 7 hours, the lower limit of the "
            "commonly recommended 7 to 9 hours for adults. The other events are defined from the Phase 1 variables."),
          ] + make_table(ev_rows,
                         ["Event", "Definition (observation in the data)", "Adults (n)", "P (sample)", "P (weighted)"],
                         [1.4, 3.0, 0.8, 0.8, 0.9], "Events used in Phase 2.")
    S += [
        P("We use three random variables. <b>Y</b> is the HbA1c value (%) of an adult chosen at random from the sample "
          "(continuous). <b>I<sub>B</sub></b> is the indicator of event B for that adult (Bernoulli). <b>K</b> is the number "
          "of adults with event B among 90 adults drawn at random (discrete; binomial under simple random sampling).")]

    # -------------------------------------------------------------- 2
    j = joint
    S += [P("2. Marginal and Joint Probabilities", "h1"),
          P(f"The marginal probabilities are P(A) = {pc(j.loc['P(A) marginal', 'joint_probability'])} and "
            f"P(B) = {pc(j.loc['P(B) marginal', 'joint_probability'])}. The joint probability that an adult has both short sleep "
            f"and a high HbA1c is P(A and B) = {pc(j.loc['A and B', 'joint_probability'], 2)} ({int(j.loc['A and B', 'n'])} adults), "
            f"compared with {pc(j.loc['A and B', 'expected_if_independent'], 2)} that would be expected if A and B were independent "
            f"(Table 2).")]
    j_rows = [[c, f"{int(r.n):,}", f"{r.joint_probability:.4f}",
               "" if pd.isna(r.expected_if_independent) else f"{r.expected_if_independent:.4f}"] for c, r in
              joint.iterrows()]
    S += make_table(j_rows, ["Cell", "Adults (n)", "Empirical probability", "Expected if independent, P(A) x P(B)"],
                    [2.0, 1.1, 1.6, 2.2], "Joint and marginal probabilities of short sleep (A) and high HbA1c (B).")

    # -------------------------------------------------------------- 3
    c_rows = [[g, f"{int(r.n):,}", pc(r.p_b_given_unweighted), f"{r.ratio_to_overall:.2f}", pc(r.p_b_given_weighted),
               f"{r.ratio_to_overall_weighted:.2f}"] for g, r in cond.iterrows()]
    S += [P("3. Conditional Probabilities", "h1"),
          P(f"Conditioning on a characteristic restricts attention to the adults who have it and re-computes the probability "
            f"within that group: P(B | G) = P(B and G) / P(G). Overall, P(B) = {pc(pB)}. Among adults with no leisure-time activity, "
            f"P(B | inactive) = {pc(cond.loc['no leisure-time activity', 'p_b_given_unweighted'])}, "
            f"{cond.loc['no leisure-time activity', 'ratio_to_overall']:.2f} times the overall probability, whereas among adults "
            f"with recommended sleep it is {pc(cond.loc['recommended sleep (7 to <9 h)', 'p_b_given_unweighted'])}. "
            f"Obesity raises the probability to {pc(cond.loc['obesity (BMI >= 30)', 'p_b_given_unweighted'])} "
            f"(versus {pc(cond.loc['no obesity (BMI < 30)', 'p_b_given_unweighted'])} without obesity), and age 60 or older to "
            f"{pc(cond.loc['age >= 60', 'p_b_given_unweighted'])}. Sleep shows a U-shaped pattern: the probability is lower with "
            f"recommended sleep than with either short or long sleep (Table 3, Figure 1).")]
    S += make_table(c_rows,
                    ["Given (G)", "Adults (n)", "P(B | G)", "Ratio to P(B)", "P(B | G), weighted", "Ratio, weighted"],
                    [2.0, 0.8, 0.9, 0.9, 1.3, 1.0],
                    "Conditional probability of a high HbA1c (B) given each characteristic.")
    S += [figure("p2_fig1_conditional_probabilities.png",
                 "Probability of HbA1c >= 6.5% by sleep, activity, BMI, and age group (unweighted). The dashed line is the "
                 "overall probability.", width=5.6)]

    # -------------------------------------------------------------- 4
    i_rows = [[EVENT_LABELS[e], f"{r['P(A and B)']:.4f}", f"{r['P(A) x P(B)']:.4f}", f"{r['joint / expected']:.2f}",
               pc(r['P(B|A)']), f"{100 * r['P(B|A) - P(B)']:+.1f}"] for e, r in ind.iterrows()]
    s_rows = [[r.age_group, f"{int(r.n):,}", pc(r._3), pc(r._4), pc(r._5)] for r in ssa.itertuples()]
    S += [P("4. Independence", "h1"),
          P("Events A and B are independent if P(A and B) = P(A) x P(B), equivalently P(B | A) = P(B). We compare the observed "
            "joint probability with the product of the marginals (Table 4); a ratio near 1 is consistent with independence. "
            f"For short sleep the ratio is {ind.loc['short_sleep', 'joint / expected']:.2f} and P(B | short sleep) differs from P(B) "
            f"by only {100 * ind.loc['short_sleep', 'P(B|A) - P(B)']:.1f} percentage points, so the data appear roughly consistent "
            f"with independence. For long sleep, inactivity, obesity, and age 60 or older the ratios are "
            f"{ind.loc['long_sleep', 'joint / expected']:.2f} to {ind.loc['inactive', 'joint / expected']:.2f}, which is not "
            "consistent with independence. No formal test is performed in this phase, so 'consistent' does not mean "
            "'proven independent': sampling variability could hide a weak association, and a third variable can hide or create "
            "one. Table 5 conditions on age group: within each age group the probability of B is slightly higher among short "
            "sleepers, so the weak overall pattern is not an artifact of age, but the differences are small.")]
    S += make_table(i_rows, ["Event A", "P(A and B)", "P(A) x P(B)", "Ratio", "P(B | A)", "P(B|A) - P(B) (pp)"],
                    [1.6, 0.9, 0.9, 0.7, 0.8, 1.3], "Observed joint probability versus the product of marginals.")
    S += make_table(s_rows,
                    ["Age group", "Adults (n)", "P(short sleep)", "P(B | short sleep)", "P(B | not short sleep)"],
                    [1.1, 1.0, 1.2, 1.5, 1.7], "Short sleep and high HbA1c within age groups.")

    # -------------------------------------------------------------- 5
    sd_cl = cl["p"].std()
    b_rows = [[r.scenario, f"{r.mean_of_counts:.2f}", f"{r.variance_of_counts:.2f}", f"{r.binomial_mean:.2f}",
               f"{r.binomial_variance:.2f}", f"{r.variance_ratio_to_binomial:.2f}"] for r in bs.itertuples()]
    S += [P("5. Discrete Distribution and the Binomial Model", "h1"),
          P(f"A binomial model Bin(n, p) describes the number K of 'successes' in n trials if (i) n is fixed, (ii) each trial has "
            f"two outcomes, (iii) trials are independent, and (iv) the probability p is the same in every trial. We take the event "
            f"B (HbA1c >= 6.5%) with p = {pB:.4f} and ask whether the number of adults with B in equal-sized subsamples of 90 "
            f"adults behaves as Bin(90, {pB:.3f}); the expected count is {90 * pB:.2f} and the variance {90 * pB * (1 - pB):.2f}."),
          P(f"<b>Random subsamples.</b> We drew 10,000 simple random subsamples of 90 adults from the analytic sample. The empirical "
            f"distribution of K matches the binomial probabilities closely (Figure 2a); the variance of K is "
            f"{bs.iloc[0]['variance_of_counts']:.2f} versus {bs.iloc[0]['binomial_variance']:.2f} for the binomial "
            f"(ratio {bs.iloc[0]['variance_ratio_to_binomial']:.2f}). The small shortfall is the finite-population effect: sampling without "
            f"replacement from 5,490 adults gives the hypergeometric variance {bs.iloc[0]['hypergeometric_variance']:.2f}. For random "
            f"subsamples all four assumptions hold, so the binomial model is a good approximation."),
          P(f"<b>Subsamples within design clusters.</b> NHANES is a cluster sample. We formed {len(cl)} clusters (masked stratum x PSU) "
            f"and drew a random subsample of 90 adults within each, repeating this 1,000 times. The variance of the 30 counts is on "
            f"average {disp:.2f} times the binomial variance (Figure 2b), i.e., the counts are over-dispersed. The reason is that p "
            f"is not the same in every cluster: the cluster proportions range from {pc(cl['p'].min())} to {pc(cl['p'].max())} "
            f"(SD {pc(sd_cl)}). Hence the binomial assumptions of independence and a common p fail for the survey data as a "
            f"whole; in addition, unequal sampling weights mean that adults do not represent equal shares of the population. "
            f"This is why Phase 3 will use methods that account for the design (Table 6).")]
    S += make_table(b_rows, ["Scenario", "Mean of counts", "Variance of counts", "Binomial mean", "Binomial variance",
                             "Variance ratio"],
                    [2.6, 0.8, 0.8, 0.8, 0.9, 0.8],
                    "Counts of adults with HbA1c >= 6.5% in subsamples of 90, compared with Bin(90, 0.124).")
    S += [figure("p2_fig3_binomial_vs_empirical.png",
                 "(a) Distribution of the count in 10,000 random subsamples of 90 adults and the binomial probabilities. (b) Ratio of "
                 "the variance of cluster counts to the binomial variance in 1,000 repetitions; the dashed line marks ratio 1.",
                 width=6.2)]

    # -------------------------------------------------------------- 6
    n_rows = []
    for r in na.itertuples():
        ref = str(r.variable).startswith("Normal")
        n_rows.append([r.variable, "" if ref else r.scale, f"{r.skewness:.2f}", f"{r.excess_kurtosis:.2f}",
                       f"{r.pct_within_1sd:.1f}", f"{r.pct_within_2sd:.1f}", f"{r.pct_within_3sd:.1f}",
                       "" if ref else f"{int(r.n_beyond_3sd)}", f"{r.qq_correlation:.3f}"])
    S += [P("6. Continuous Variables and the Normal Distribution", "h1"),
          P("We assess the normal approximation for sleep, BMI, and HbA1c with histograms overlaid by the normal density with the same "
            "mean and SD, normal Q-Q plots, skewness and excess kurtosis, and the share of values within 1, 2, and 3 SD of the mean "
            "(68.3%, 95.4%, and 99.7% under normality) (Table 7, Figures 3 to 5). A test of normality alone would be uninformative here: with "
            "5,490 observations it would reject for any small departure."),
          P("<b>Sleep</b> is nearly symmetric (skewness -0.16) but more peaked than a normal distribution (75.5% within 1 SD), which probably reflects "
            "that adults report round values such as 7 or 8 hours; the normal approximation is acceptable for describing its center. "
            "<b>BMI</b> is right-skewed (1.23) and the Q-Q plot curves upward in the right tail; the natural logarithm reduces the "
            "skewness to 0.44 and the Q-Q correlation increases from 0.964 to 0.995, so BMI is approximately normal on the log scale. "
            "<b>HbA1c</b> is strongly right-skewed (3.56) with very heavy tails (excess kurtosis 18.1) and 139 values beyond 3 SD, "
            "all of them on the high side (up to 17.1%); the log transformation does not repair this (skewness 2.30), so a normal model is not appropriate "
            "for HbA1c itself and the median and IQR remain the right summaries. These very high values are genuine measurements and "
            "are retained.")]
    S += make_table(n_rows, ["Variable", "Scale", "Skewness", "Excess kurtosis", "% within 1 SD", "% within 2 SD",
                             "% within 3 SD",
                             "n beyond 3 SD", "Q-Q r"], [1.5, 0.8, 0.65, 0.7, 0.7, 0.7, 0.7, 0.65, 0.55],
                    "Checks of the normal approximation (analytic sample).")
    S += [figure("p2_fig4_normal_sleep.png",
                 "Sleep duration: histogram with normal density (left) and normal Q-Q plot (right).", width=5.0),
          figure("p2_fig5_normal_bmi.png",
                 "BMI on the raw (top) and natural-log (bottom) scale: histogram with normal density and Q-Q plot.",
                 width=5.0),
          figure("p2_fig6_normal_hba1c.png",
                 "HbA1c on the raw (top) and natural-log (bottom) scale: histogram with normal density and Q-Q plot.",
                 width=5.0)]

    # -------------------------------------------------------------- 7
    e_rows = [[r.random_variable, r.unit, f"{r.expectation:.4f}", f"{r.variance:.4f}", f"{r.sd:.4f}",
               f"{r.expectation_weighted:.4f}", f"{r.variance_weighted:.4f}"] for r in evv.itertuples()]
    S += [P("7. Expectation and Variance", "h1"),
          P("For the empirical distribution, the expectation E is the mean of the variable and the variance Var is the average squared "
            "deviation from the mean (sample variance with divisor n - 1; weighted version with the sampling weights). "
            f"For the indicator I<sub>B</sub>, E = P(B) = {pB:.4f} and Var = P(B)(1 - P(B)) = {pB * (1 - pB):.4f}. For the count K in 90 "
            f"adults, E(K) = 90 P(B) = {90 * pB:.2f} adults and Var(K) = 90 P(B)(1 - P(B)) = {90 * pB * (1 - pB):.2f} (SD "
            f"{(90 * pB * (1 - pB)) ** 0.5:.2f}): in a random group of 90 adults we expect about 11 to have a diabetes-range HbA1c, "
            f"typically within a few adults of that number. The average HbA1c of an adult is "
            f"{evv.iloc[2]['expectation']:.2f}% with variance {evv.iloc[2]['variance']:.2f} (%<super>2</super>), i.e., SD "
            f"{evv.iloc[2]['sd']:.2f}%; the variance is in squared units, so the SD is easier to interpret. Weighted expectations "
            f"estimate population quantities and are slightly lower (for example, {evv.iloc[0]['expectation_weighted']:.4f} for "
            f"I<sub>B</sub>) because the weighted population is younger.")]
    S += make_table(e_rows, ["Random variable", "Unit", "Expectation", "Variance", "SD", "Expectation (weighted)",
                             "Variance (weighted)"],
                    [2.4, 0.7, 0.8, 0.7, 0.6, 0.9, 0.8], "Expectation and variance of the main random variables.")

    # -------------------------------------------------------------- 8
    cv_rows = []
    for r in cov.itertuples():
        names = {"BMXBMI": "BMI", "LBXGH": "HbA1c", "sleep_hours": "Sleep", "mvpa_min_week": "Leisure-time MVPA",
                 "sedentary_hours": "Sedentary time"}
        cv_rows.append([f"{names[r.x]} and {names[r.y]}", f"{r.covariance:.4f}", r.unit, r.direction])
    S += [P("8. Two Random Variables and Covariance", "h1"),
          P("The sample covariance of two variables is the average product of their deviations from their means (divisor n - 1). A positive "
            "covariance means that above-average values of one variable tend to occur with above-average values of the other; a negative "
            "covariance means the opposite. BMI and HbA1c have a positive covariance (1.61), and leisure-time activity has a negative "
            "covariance with both HbA1c (-23.9) and BMI (-349.6): adults who are more active tend to have lower HbA1c and lower BMI. "
            "The covariance of sleep and HbA1c is close to zero (0.04), which is consistent with the U-shaped pattern found earlier, "
            "because covariance only measures linear co-movement. Covariances depend on the units of measurement (Table 9), so their "
            "sizes cannot be compared across pairs; the correlation coefficient, which removes the units, is studied in Phase 4. "
            "These relationships are not causal (Figure 6).")]
    S += make_table(cv_rows, ["Pair", "Covariance", "Unit", "Direction"], [2.6, 1.1, 1.6, 1.0],
                    "Sample covariances (analytic sample, unweighted).")
    S += [figure("p2_fig7_scatter_covariance.png",
                 "Scatter plots of HbA1c against BMI, average sleep, and leisure-time activity (the activity axis uses a symmetric "
                 "logarithmic scale for readability; the covariance in the title uses the original units).", width=6.3)]

    # -------------------------------------------------------------- 9
    bu, bw = bayes.loc["unweighted"], bayes.loc["weighted"]
    by_rows = [["Adults used (n)", f"{int(bu['n']):,}", f"{int(bw['n']):,}"],
               ["Prior P(D)", f"{bu['P(D) prior']:.4f}", f"{bw['P(D) prior']:.4f}"],
               ["Likelihood P(B | D)", f"{bu['P(B|D)']:.4f}", f"{bw['P(B|D)']:.4f}"],
               ["Likelihood P(B | not D)", f"{bu['P(B|not D)']:.4f}", f"{bw['P(B|not D)']:.4f}"],
               ["Total probability P(B)", f"{bu['P(B) total probability']:.4f}", f"{bw['P(B) total probability']:.4f}"],
               ["Posterior P(D | B) by Bayes' theorem", f"{bu['P(D|B) by Bayes']:.4f}", f"{bw['P(D|B) by Bayes']:.4f}"],
               ["P(D | B) computed directly", f"{bu['P(D|B) direct']:.4f}", f"{bw['P(D|B) direct']:.4f}"],
               ["P(not D | B): high HbA1c without a diagnosis", f"{bu.iloc[-1]:.4f}", f"{bw.iloc[-1]:.4f}"]]
    S += [P("9. Bayes' Theorem", "h1"),
          P("Let D be a self-reported diagnosis of diabetes and B a high HbA1c. Bayes' theorem updates the prior probability of D after "
            "observing B: P(D | B) = P(B | D) P(D) / [P(B | D) P(D) + P(B | not D) P(not D)]. Participants with borderline diabetes "
            f"(DIQ010 = 3) are excluded from this calculation, leaving {int(bu['n']):,} adults. The prior is P(D) = {pc(bu['P(D) prior'])}; "
            f"{pc(bu['P(B|D)'])} of adults with a diagnosis have a high HbA1c (the remainder are probably treated and controlled) and "
            f"{pc(bu['P(B|not D)'])} of adults without a diagnosis do. Bayes' theorem gives P(D | B) = {pc(bu['P(D|B) by Bayes'])}, which "
            f"equals the directly computed proportion, as it must when empirical frequencies are used. Thus about "
            f"{pc(bu.iloc[-1])} of adults with a diabetes-range HbA1c report no diagnosis. Both the laboratory value and the "
            "self-reported diagnosis are imperfect indicators of diabetes, so the figure describes agreement between the two, not "
            "the prevalence of undiagnosed diabetes (Table 10).")]
    S += make_table(by_rows, ["Quantity", "Unweighted", "Weighted"], [3.6, 1.2, 1.2],
                    "Bayes' theorem for the probability of a diagnosed diabetes given a high HbA1c.")

    # -------------------------------------------------------------- Track A
    S += [P("Track A Requirements", "h1")]
    sg_rows = [[r.variable, r.group, f"{int(r.n):,}", f"{int(r.n_events):,}", pc(r.p_unweighted), pc(r.p_weighted),
                f"{r.diff_from_overall_pp:+.1f}"] for r in sg.itertuples()]
    age_rows = sg[sg["variable"] == "age_group"].set_index("group")
    sex_rows = sg[sg["variable"] == "sex"].set_index("group")
    S += [P("A.1 Conditional probability in subgroups", "h2"),
          P(f"The probability of a high HbA1c (B) varies strongly with age: {pc(age_rows.loc['20-39', 'p_unweighted'])} at ages 20-39, "
            f"{pc(age_rows.loc['40-59', 'p_unweighted'])} at 40-59, and {pc(age_rows.loc['60+', 'p_unweighted'])} at 60 or older. It is "
            f"{pc(sex_rows.loc['Male', 'p_unweighted'])} in men and {pc(sex_rows.loc['Female', 'p_unweighted'])} in women (Table 11). "
            "Differences between subgroups are only described here; no hypothesis test has been performed.")]
    S += make_table(sg_rows, ["Variable", "Group", "n", "Events", "P(B), sample", "P(B), weighted",
                              "Difference from overall (pp)"],
                    [0.9, 1.9, 0.6, 0.6, 0.9, 0.9, 1.2], "Probability of HbA1c >= 6.5% by subgroup.")
    S += [P("A.2 Binomial model for a count", "h2"),
          P("The event is an HbA1c of at least 6.5%, a clinical threshold. The behavior of its count in equal-sized subsamples of 90 adults "
            "is compared with Bin(90, 0.124) in Section 5, Table 6, and Figure 2: the model fits random subsamples well but fails for "
            "subsamples within design clusters (variance ratio 1.77) because the probability differs between clusters.")]
    S += [P("A.3 Shape of a health measurement", "h2"),
          P("Section 6 examines BMI and HbA1c (and sleep). BMI is right-skewed but approximately normal after a log transformation; HbA1c has "
            "extreme skewness, heavy tails, and 139 observations beyond 3 SD, so a normal approximation is not appropriate.")]
    S += [P("A.4 Role of the sampling weights in empirical probability", "h2"),
          P(f"The sample frequency of a high HbA1c is {pc(pB)}, but the weighted estimate of the population probability is {pc(pBw)}. A "
            f"frequency in the sample describes the sample; an estimate of a population probability must give each adult the weight "
            f"he or she represents. Older adults were oversampled and have a higher probability of B, so the sample overstates the "
            f"population probability. The age-specific probabilities change little with weighting (for ages 60 or older "
            f"{pc(we.loc['P(B | age 60+)', 'unweighted'])} unweighted and {pc(we.loc['P(B | age 60+)', 'weighted'])} weighted); the difference "
            f"in the overall figure comes from the age composition. Applying the weighted age distribution to the sample's age-specific "
            f"probabilities gives {pc(we.loc['P(B) standardized to the weighted age distribution', 'unweighted'])}, close to the weighted "
            f"{pc(pBw)} (Table 12, Figure 7).")]
    w_rows = [[q, pc(r.unweighted, 2), pc(r.weighted, 2)] for q, r in we.iterrows()]
    S += make_table(w_rows, ["Quantity", "Unweighted (sample)", "Weighted (population)"], [3.8, 1.5, 1.5],
                    "Empirical probabilities with and without sampling weights. For the standardized row, the first column applies the "
                    "weighted age distribution to the unweighted age-specific probabilities.")
    S += [figure("p2_fig2_weighted_vs_unweighted.png",
                 "Probability of HbA1c >= 6.5% overall and in subgroups, with and without sampling weights.",
                 width=5.4)]

    S += [P("Limitations", "h1"),
          P("(1) Probabilities are empirical frequencies of one cross-sectional sample and carry sampling error that is not quantified "
            "until Phase 3. (2) The cutoffs (HbA1c 6.5%, sleep 7 and 9 hours, BMI 30) are conventional, and results for event B depend on "
            "them; alternative definitions are examined in Phase 5. (3) The binomial and normal models are approximations; the survey "
            "design (clustering and unequal weights) violates the independence and identical-distribution assumptions of the binomial model. "
            "(4) HbA1c is influenced by diabetes treatment and other conditions, and the self-reported diagnosis is imperfect. "
            "(5) Covariances describe linear co-movement and are unit-dependent; they say nothing about causation.")]
    S += [P("Reproducibility", "h1"),
          P("All tables and figures are produced by <font face='Courier'>src/07_probability_events.py</font> and "
            "<font face='Courier'>src/08_distributions.py</font> from the analytic sample built in Phase 1 (random seed 2026), and this "
            "report by <font face='Courier'>src/09_build_phase2_report.py</font>.")]
    return S


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUT_PATH), pagesize=letter, leftMargin=0.85 * inch, rightMargin=0.85 * inch,
                            topMargin=0.8 * inch, bottomMargin=0.85 * inch,
                            title="Phase 2 Report - NHANES 2021-2023: Probability and Distributions")
    doc.build(build_story(load()), onFirstPage=footer, onLaterPages=footer)
    print(f"Report written to {OUT_PATH}")


if __name__ == "__main__":
    main()
