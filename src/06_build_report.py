"""Phase 1 - Step 6: Build the Phase 1 report (PDF) from the saved tables and figures.

Inputs
------
reports/phase1/tables/*.csv and figures/phase1/*.png (created by scripts 01-05)

Output
------
reports/phase1/phase1_report.pdf
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
from reportlab.platypus import (
    Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TABLES_DIR = PROJECT_ROOT / "reports" / "phase1" / "tables"
FIG_DIR = PROJECT_ROOT / "figures" / "phase1"
OUT_PATH = PROJECT_ROOT / "reports" / "phase1" / "phase1_report.pdf"

AUTHOR_LINE = "[Kiarash Hajizadeh]"  # <- edit before submission

# ----------------------------------------------------------------------------- styles
base = getSampleStyleSheet()
STY = {
    "title": ParagraphStyle("title", parent=base["Title"], fontSize=17, leading=21, spaceAfter=6),
    "subtitle": ParagraphStyle("subtitle", parent=base["Normal"], fontSize=11, leading=14,
                               alignment=1, textColor=colors.HexColor("#444444")),
    "h1": ParagraphStyle("h1", parent=base["Heading1"], fontSize=13.5, leading=17,
                         spaceBefore=12, spaceAfter=5),
    "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=11, leading=14,
                         spaceBefore=8, spaceAfter=3),
    "body": ParagraphStyle("body", parent=base["Normal"], fontSize=10, leading=13.5,
                           alignment=TA_JUSTIFY, spaceAfter=6),
    "caption": ParagraphStyle("caption", parent=base["Normal"], fontSize=8.5, leading=11,
                              textColor=colors.HexColor("#333333"), spaceBefore=2, spaceAfter=8),
    "cell": ParagraphStyle("cell", parent=base["Normal"], fontSize=7.8, leading=9.5),
    "cellb": ParagraphStyle("cellb", parent=base["Normal"], fontSize=7.8, leading=9.5,
                            fontName="Helvetica-Bold"),
}

_counter = {"table": 0, "figure": 0}


def P(text, style="body"):
    return Paragraph(text, STY[style])


def E(text):
    return escape(str(text))


# ----------------------------------------------------------------------------- helpers
def make_table(rows, header, widths, caption):
    """rows: list of lists of already-formatted strings (will be escaped)."""
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
    # Keep short tables on one page; long tables may break across pages (header repeats).
    return [KeepTogether(items)] if len(rows) <= 14 else items


def figure(filename, caption, width=4.9):
    _counter["figure"] += 1
    path = FIG_DIR / filename
    iw, ih = ImageReader(str(path)).getSize()
    img = Image(str(path), width=width * inch, height=width * inch * ih / iw)
    cap = Paragraph(f"<b>Figure {_counter['figure']}.</b> {caption}", STY["caption"])
    return KeepTogether([img, cap])


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(0.85 * inch, 0.55 * inch, "Phase 1 Report - NHANES 2021-2023: Sleep, Physical Activity, and HbA1c")
    canvas.drawRightString(letter[0] - 0.85 * inch, 0.55 * inch, f"Page {doc.page}")
    canvas.restoreState()


# ----------------------------------------------------------------------------- data
VAR_NAMES = {
    "RIDAGEYR": "Age (years)",
    "LBXGH": "HbA1c (%)",
    "BMXBMI": "BMI (kg/m2)",
    "sleep_hours": "Sleep (h/day)",
    "mod_min_week": "Moderate activity (min/wk)",
    "vig_min_week": "Vigorous activity (min/wk)",
    "mvpa_min_week": "MVPA total (min/wk)",
    "sedentary_hours": "Sedentary time (h/day)",
    "INDFMPIR": "Income-poverty ratio",
}
CAT_NAMES = {
    "sex": "Sex", "age_group": "Age group (years)", "race_eth": "Race / Hispanic origin",
    "education": "Education", "diabetes_dx": "Diagnosed diabetes", "bmi_cat": "BMI category",
    "sleep_cat": "Sleep category", "mvpa_cat": "Activity category",
}
GROUP_NAMES = {"sleep_cat": "Sleep", "mvpa_cat": "Leisure-time MVPA", "bmi_cat": "BMI"}


def load():
    t = {p.stem: pd.read_csv(p) for p in TABLES_DIR.glob("*.csv")}
    return t


def build_story(t):
    flow = t["sample_flow"]
    n_all = int(flow.iloc[0]["n_remaining"])
    n_adults = int(flow.iloc[1]["n_remaining"])
    n_exam = int(flow.iloc[2]["n_remaining"])
    n_nonpreg = int(flow.iloc[3]["n_remaining"])
    n_final = int(flow.iloc[-1]["n_remaining"])
    wsum = t["weight_summary"]
    pop_m = float(wsum.loc[wsum["weight"] == "WTPH2YR", "sum_millions"].iloc[0])
    wg = t["weights_by_group"]
    old = wg[(wg["variable"] == "age_group") & (wg["group"] == "60+")].iloc[0]
    rvw = t["raw_vs_weighted_numeric"].set_index("variable")
    cat = t["raw_vs_weighted_categorical"]
    diab = cat[(cat["variable"] == "diabetes_dx") & (cat["category"] == "Yes")].iloc[0]
    pct_exam = 100 * n_exam / n_adults

    S = []

    # ------------------------------------------------------------------ title block
    S += [Spacer(1, 6),
          P("Sleep Duration, Physical Activity, and Glycated Hemoglobin Among U.S. Adults", "title"),
          P("Analysis of NHANES August 2021 - August 2023", "subtitle"),
          P("<b>Phase 1 Report: Understanding the Study, the Data, and Descriptive Statistics</b>", "subtitle"),
          Spacer(1, 4), P(f"{E(AUTHOR_LINE)} &nbsp;|&nbsp; Statistics Course Project, Fall 1405 &nbsp;|&nbsp; Track A (NHANES)", "subtitle"),
          Spacer(1, 10)]

    # ------------------------------------------------------------------ summary
    S += [P("Summary", "h1"),
          P(f"This report documents Phase 1 of a project that examines whether habitual sleep duration and "
            f"leisure-time physical activity are associated with glycated hemoglobin (HbA1c) and body mass index (BMI) "
            f"among U.S. adults. We merged six NHANES 2021-2023 files ({n_all:,} participants) and defined an analytic "
            f"population of {n_final:,} non-pregnant adults aged 20 years or older with complete data on HbA1c, BMI, sleep, "
            f"leisure-time activity, and sedentary time. Because NHANES is a complex probability sample in which older adults "
            f"were oversampled, we report both unweighted and weighted summaries: adults aged 60 or older make up "
            f"{old['pct_of_sample']:.1f}% of the sample but {old['pct_of_population']:.1f}% of the weighted population "
            f"(about {pop_m:.0f} million adults). HbA1c and physical activity are strongly right-skewed, so medians and "
            f"interquartile ranges are the appropriate summaries. In purely descriptive comparisons, mean HbA1c was higher "
            f"among adults who reported short or long sleep, no leisure-time activity, or obesity. These observations are "
            f"not tested here and are not adjusted for age or diabetes; inference begins in Phase 3.")]

    # ------------------------------------------------------------------ 1
    S += [P("1. Data Source and Collection Mechanism", "h1"),
          P("The National Health and Nutrition Examination Survey (NHANES) is a program of cross-sectional surveys run by the "
            "National Center for Health Statistics (NCHS) of the U.S. Centers for Disease Control and Prevention (CDC). "
            "Participants complete a household interview and then attend a standardized examination, with blood and urine "
            "specimens, in a mobile examination center (MEC). We use the August 2021 - August 2023 cycle, the first national "
            "release after the interruption of NHANES by the COVID-19 pandemic. The files are public-use SAS transport files "
            "downloaded from the CDC website; no access restrictions apply."),
          P("Our variables come from three different mechanisms: (i) <b>interviewer-administered questionnaires</b> for sleep "
            "duration, leisure-time physical activity, sedentary time, and diagnosed diabetes (self-reported); (ii) "
            "<b>physical examination</b> for height and weight, from which BMI is computed; and (iii) <b>laboratory "
            "measurement</b> of HbA1c in blood. The data are therefore the product of an observational survey, not of a "
            "randomized experiment.")]

    # ------------------------------------------------------------------ 2
    mc = t["merge_counts"]
    rows = [[r.file, f"{r.n_rows:,}", f"{r.n_unique_seqn:,}", f"{r.n_seqn_found_in_demo:,}", str(r.n_columns)]
            for r in mc.itertuples()]
    rows.append(["After merge (left join on SEQN)", f"{n_all:,}", f"{n_all:,}", f"{n_all:,}", "71 (incl. one SEQN)"])
    S += [P("2. Unit of Observation and Data Structure", "h1"),
          P("One row represents one participant, identified by <b>SEQN</b>. In every file SEQN is unique, so there is exactly "
            "one record per person and no repeated measurements. The structure is hierarchical only in the sampling design "
            "(participants are nested in primary sampling units, which are nested in strata), not in the rows. "
            "Not every participant has every component: DEMO_L covers all participants, whereas BMX_L covers only those "
            "examined, and GHB_L only those with an eligible blood draw (Table 1)."),
          ] + make_table(rows, ["File", "Rows", "Unique SEQN", "SEQN found in DEMO_L", "Columns"],
                         [2.4, 0.9, 1.1, 1.5, 1.2],
                         "Participants per file before merging and in the merged file. "
                         "All six files were merged with DEMO_L as the base file (left joins, one-to-one validated); "
                         "the merged file keeps all participants and has 71 columns (76 minus five duplicated SEQN columns).")

    # ------------------------------------------------------------------ 3
    S += [P("3. Sampling, Selection, and Generalizability", "h1"),
          P("NHANES uses a stratified, multistage cluster probability sample of the U.S. civilian noninstitutionalized "
            "population. Participants therefore have unequal probabilities of selection. According to the DEMO_L "
            "documentation, this cycle oversampled persons by age group and did not oversample by "
            "race and Hispanic origin or by income. Selection into our analysis has three layers: (i) the survey sample itself; "
            f"(ii) participation in the examination - {n_exam:,} of {n_adults:,} adults ({pct_exam:.1f}%) were examined in the "
            f"MEC; and (iii) availability of all key variables ({n_final:,} of {n_nonpreg:,} eligible non-pregnant adults)."),
          P("Because the study is observational, associations cannot be interpreted causally. Results from the weighted "
            "analyses can be generalized to U.S. civilian noninstitutionalized adults aged 20 or older during 2021-2023, "
            "subject to nonresponse and the complete-case restriction; results from unweighted analyses describe the analytic "
            "sample only. Institutionalized and military populations are not represented.")]

    # ------------------------------------------------------------------ 4
    var_rows = [
        ["LBXGH", "HbA1c (glycated hemoglobin), %", "Quantitative, continuous", "Response (primary)"],
        ["BMXBMI", "Body mass index, kg/m2", "Quantitative, continuous", "Response (secondary); adjustment variable"],
        ["sleep_hours", "Weekly average sleep, h/day = (5 x workday + 2 x non-workday)/7 (from SLD012, SLD013)", "Quantitative, continuous (derived)", "Explanatory"],
        ["mvpa_min_week", "Leisure-time moderate + vigorous activity, min/week (from PAD790Q/U, PAD800, PAD810Q/U, PAD820)", "Quantitative, continuous, right-skewed (derived)", "Explanatory"],
        ["sedentary_hours", "Usual daily sitting time, hours (PAD680 / 60)", "Quantitative, continuous", "Explanatory"],
        ["RIDAGEYR", "Age in years (top-coded at 80)", "Quantitative, discrete", "Adjustment"],
        ["RIAGENDR", "Sex (male / female)", "Nominal, binary", "Adjustment"],
        ["RIDRETH3", "Race and Hispanic origin (6 categories)", "Nominal", "Adjustment"],
        ["DIQ010", "Diagnosed diabetes (yes / no / borderline)", "Nominal", "Stratification / sensitivity"],
        ["sleep_cat, mvpa_cat, bmi_cat, age_group", "Categorized versions of sleep, activity, BMI, and age", "Ordinal (derived)", "Grouping (descriptive, ANOVA)"],
        ["WTPH2YR, SDMVSTRA, SDMVPSU", "Phlebotomy weight; masked variance stratum; masked PSU", "Quantitative / design identifiers", "Survey design"],
    ]
    S += [P("4. Classification of Variables", "h1"),
          P("Table 2 lists the main variables, their measurement scale, and their role. The scale determines the summary statistics, "
            "graphs, and methods used in later phases: quantitative variables are summarized by means or medians and shown in "
            "histograms or box plots, and ordinal categories are used for group comparisons.")]
    S += make_table(var_rows, ["Variable", "Description", "Type / scale", "Role"], [1.25, 3.0, 1.55, 1.3],
                    "Main variables, measurement scales, and roles.")

    # ------------------------------------------------------------------ 5
    miss = t["missingness_adults"]
    miss_rows = [[r.variable, r.description, f"{r.n_missing:,}", f"{r.pct_missing:.2f}"] for r in miss.itertuples()]
    sp = t["special_code_recoding"]
    sp_rows = [[r.variable, r.codes.replace("[", "").replace("]", ""), f"{r.n_set_to_missing:,}"] for r in sp.itertuples()]
    qc = t["quality_checks"]
    qc_rows = [[r.check, f"{r.n_flagged:,}"] for r in qc.itertuples()]
    dec = [
        ["Refused / don't know codes (7777, 9999; 7, 9)", "Set to missing; complete-case analysis.", "These are not valid measurements; their number is small (Table 4)."],
        ["Zero stored as ~5e-79 (PAD790Q, PAD810Q, PAD680)", "Converted to exact 0.", "These are real zeros (no activity, no sitting); dropping them would remove the least active adults."],
        ["Sleep < 3 h or > 12 h per day (63)", "Retained.", "Plausible self-reports within the allowed range; examined in Phase 5."],
        ["Sedentary time = 0 min (3) or >= 18 h (22)", "Retained and flagged.", "Within the allowed range but implausible; no prespecified scientific rule for deletion; sensitivity analysis in Phase 5."],
        ["MVPA > 2520 min/week (48)", "Retained and flagged.", "Possible for physically demanding activity; no value exceeds 24 h/day; sensitivity analysis in Phase 5."],
        ["Pregnant participants (41)", "Excluded.", "Pregnancy affects BMI and HbA1c. Women whose pregnancy status could not be determined (code 3) were retained."],
        ["Income-to-poverty ratio missing (13.1%)", "Not used in the primary models.", "Including it would drop about 800 adults; may be used in a sensitivity analysis."],
        ["Age 80+ top-coded; income ratio top-coded at 5", "Retained.", "Documented limitation of the public-use files."],
        ["Duplicate SEQN; logical inconsistencies", "None found.", "See Table 5."],
    ]
    S += [P("5. Data Quality Audit", "h1"),
          P(f"We audited the {n_nonpreg:,} adults who were examined and not pregnant. The main source of missingness is HbA1c "
            "(4.9%), which is measured only in participants who provided an eligible blood sample; BMI, sleep, activity, and "
            "sitting time each have about 1% missing. Because we analyze complete cases, the analytic sample is somewhat smaller "
            "than the eligible population, and the weights were not re-adjusted for this additional item nonresponse.")]
    S += make_table(miss_rows, ["Variable", "Description", "Missing (n)", "Missing (%)"], [1.3, 2.9, 1.0, 1.0],
                    f"Missing data among {n_nonpreg:,} adults (age 20 or older, examined, not pregnant).")
    S += make_table(sp_rows, ["Variable", "Codes set to missing", "Records (n)"], [1.6, 2.2, 1.2],
                    "Special codes (refused / don't know) recoded to missing in the merged file (all ages).")
    S += make_table(qc_rows, ["Check", "Records flagged (n)"], [4.6, 1.4],
                    "Range, plausibility, and consistency checks (analytic sample unless stated).")
    S += [P("Table 6 gives the decision taken for each issue and the reason. Any later exclusion of observations will "
            "follow a rule stated in advance and will be reported as a sensitivity analysis rather than as a permanent deletion.")]
    S += make_table(dec, ["Issue", "Decision", "Rationale"], [2.0, 1.5, 3.6],
                    "Data-quality decisions.")

    # ------------------------------------------------------------------ 6
    ft = t["frequency_tables"]
    fr_rows = []
    for r in ft.itertuples():
        category = "Missing" if str(r.category) == "nan" else r.category
        fr_rows.append([CAT_NAMES.get(r.variable, r.variable), category, f"{r.n:,}", f"{r.percent:.1f}"])
    S += [P("6. Frequency Tables and Empirical Distributions", "h1"),
          P(f"Table 7 summarizes the categorical variables in the analytic sample (n = {n_final:,}, unweighted). "
            "The sample is slightly more female (54.9%) and older (45.8% aged 60 or older) than the U.S. adult population, "
            "consistent with the age oversampling described above. Most adults are non-Hispanic White (60.0%), and 36.9% are "
            "college graduates. Obesity (BMI of 30 or more) is common (41.0%), 59.2% of adults sleep 7 to under 9 hours, and "
            "one in five sleeps under 7 hours (20.2%) or 9 hours or more (20.6%). Diagnosed diabetes is reported by 14.0%, "
            "which matters for HbA1c because treatment lowers HbA1c and changes its interpretation.")]
    S += make_table(fr_rows, ["Variable", "Category", "n", "%"], [1.9, 2.7, 0.8, 0.7],
                    "Frequency table of categorical variables (analytic sample, unweighted). Percentages are of "
                    f"{n_final:,} adults.")

    # ------------------------------------------------------------------ 7
    ns = t["numeric_summary"]
    ns_rows = [[VAR_NAMES.get(r.variable, r.variable), f"{r.n:,}", f"{r.mean:.2f}", f"{r.sd:.2f}", f"{r.median:.2f}",
                f"{r.q1:.2f}", f"{r.q3:.2f}", f"{r.iqr:.2f}", f"{r.min:.1f}", f"{r.max:.1f}", f"{r.skewness:.2f}"]
               for r in ns.itertuples()]
    S += [P("7. Center and Spread", "h1"),
          P("Table 8 reports the mean, standard deviation, median, quartiles, interquartile range (IQR), range, and skewness "
            "of each quantitative variable. The choice of summary depends on the shape of the distribution."),
          P("<b>HbA1c</b> is strongly right-skewed (skewness 3.56): most adults have values near 5.5%, but a small group with "
            "diabetes reaches 17.1%. The median (5.5%) and IQR (0.70) describe a typical adult better than the mean (5.78%) "
            "and SD (1.09), which are pulled up by the tail. <b>Leisure-time activity</b> is even more skewed (skewness 5.65): "
            "the median is 148.9 minutes per week versus a mean of 288.7, and 18.4% of adults report none, so the median and "
            "quartiles are the appropriate summaries. <b>BMI</b> is moderately right-skewed (1.23; median 28.5, mean 29.8), "
            "so both measures are reported but the median is preferred. <b>Sleep</b> is nearly symmetric (skewness -0.16), "
            "so the mean (7.85 h) and SD (1.47 h) are appropriate. <b>Age</b> is slightly left-skewed and capped at 80, and "
            "<b>sedentary time</b> is mildly right-skewed (0.78).")]
    S += make_table(ns_rows, ["Variable", "n", "Mean", "SD", "Median", "Q1", "Q3", "IQR", "Min", "Max", "Skew"],
                    [1.75, 0.5, 0.55, 0.5, 0.58, 0.5, 0.5, 0.5, 0.5, 0.6, 0.5],
                    "Summary of quantitative variables (analytic sample, unweighted).")

    # ------------------------------------------------------------------ 8
    S += [P("8. Graphical Summaries", "h1"),
          P("Figures 1 to 6 describe the main variables. Histograms are used for continuous variables, a bar chart for the "
            "categorized activity variable, and box plots for comparisons across groups. No axis has been truncated. "
            "Weekly activity is shown in categories rather than as a histogram because its extreme skewness makes a full-range "
            "histogram unreadable."),
          figure("fig1_hba1c_hist.png",
                 "Distribution of HbA1c. The distribution is right-skewed with a long tail; dashed lines mark the commonly used "
                 "5.7% and 6.5% thresholds for prediabetes and diabetes."),
          figure("fig2_bmi_hist.png",
                 "Distribution of BMI (kg/m<super>2</super>). Dashed lines mark BMI 25 and 30; a large share of adults lies above 30."),
          figure("fig3_sleep_hist.png",
                 "Distribution of weekly average sleep duration. The distribution is roughly symmetric around 8 hours; dashed lines "
                 "mark 7 and 9 hours, the limits of the category 'recommended'."),
          figure("fig4_mvpa_categories.png",
                 "Weekly leisure-time moderate plus vigorous activity in four categories. About 18% report no activity; the value 150 "
                 "minutes per week is a commonly used activity guideline."),
          figure("fig5_hba1c_by_sleep.png",
                 "HbA1c by sleep category. Boxes show the IQR, the line the median, and the diamond the mean; points beyond the "
                 "whiskers are individual adults. Medians are similar across groups; means are higher in the short- and long-sleep "
                 "groups because of the upper tail."),
          figure("fig6_hba1c_by_bmi.png",
                 "HbA1c by BMI category. Both the median and the mean increase from the normal-weight category to obesity.")]

    # ------------------------------------------------------------------ 9
    gc = t["group_comparison"]

    def gc_rows(outcome):
        out = []
        for r in gc[gc["outcome"] == outcome].itertuples():
            out.append([GROUP_NAMES[r.group_variable], r.group, f"{r.n:,}", f"{r.mean:.2f} ({r.sd:.2f})",
                        f"{r.median:.2f} [{r.q1:.2f}, {r.q3:.2f}]", f"{r.weighted_mean:.2f}"])
        return out

    S += [P("9. Preliminary Descriptive Comparison", "h1"),
          P("Tables 9 and 10 compare HbA1c and BMI across categories of sleep, leisure-time activity, and (for HbA1c) BMI. "
            "These comparisons are purely descriptive: no test is performed and no inferential claim is made. "),
          P("Mean HbA1c is lowest among adults who sleep 7 to under 9 hours (5.71%) and higher in the short-sleep (5.83%) and "
            "long-sleep (5.96%) groups, although the medians differ little (5.5 vs 5.6%). Mean HbA1c decreases steadily with more "
            "activity, from 6.07% among inactive adults to 5.66% among those with 300 or more minutes per week, and BMI shows the "
            "same pattern (31.9 to 28.3 kg/m<super>2</super>). HbA1c rises with BMI category, from 5.53% (normal weight) to 6.02% (obesity). "
            "Weighted means are slightly lower than unweighted means because the weighted population is younger. "
            "These differences may reflect age, diagnosed diabetes (14.0% of the sample), or other factors that are not yet "
            "controlled, so they should not be interpreted as effects.")]
    S += make_table(gc_rows("LBXGH"), ["Grouping", "Category", "n", "Mean (SD)", "Median [Q1, Q3]", "Weighted mean"],
                    [1.2, 1.9, 0.6, 1.2, 1.5, 0.9], "HbA1c (%) by category of sleep, activity, and BMI.")
    S += make_table(gc_rows("BMXBMI"), ["Grouping", "Category", "n", "Mean (SD)", "Median [Q1, Q3]", "Weighted mean"],
                    [1.2, 1.9, 0.6, 1.2, 1.5, 0.9], "BMI (kg/m2) by category of sleep and activity.")

    # ------------------------------------------------------------------ 10
    S += [P("10. Final Statistical Question", "h1"),
          P("<b>Main question.</b> Among U.S. civilian noninstitutionalized adults aged 20 years or older, are habitual sleep "
            "duration and leisure-time physical activity associated with HbA1c, and does this association change after accounting "
            "for age, sex, and BMI? A secondary question examines the association of sleep and activity with BMI."),
          P("<b>Why the data are suitable.</b> HbA1c is measured by laboratory analysis rather than self-reported; the analytic "
            f"sample is large ({n_final:,} adults) with adequate numbers in each sleep and activity category (the smallest "
            "group exceeds 1,000 adults); the exposures vary widely; and sampling weights allow population-level estimates. "
            "The main limitations are the cross-sectional design, self-reported exposures, and the lack of information on diet and "
            "medication. Diagnosed diabetes will be handled as a grouping variable and removed in a sensitivity analysis "
            "(Phase 5). The question follows the Phase 1 project card and is unchanged except that the exposures are now "
            "operationally defined (Section 4).")]

    # ------------------------------------------------------------------ Track A
    S += [P("Track A Requirements", "h1")]

    S += [P("A.1 Files and merge key", "h2"),
          P(f"The files used are DEMO_L, GHB_L, SLQ_L, PAQ_L, BMX_L, and DIQ_L, merged on the shared identifier <b>SEQN</b>. "
            f"Table 1 gives the number of participants in each file before merging; after the merge there are {n_all:,} "
            "participants and no SEQN is duplicated or missing from DEMO_L.")]

    A2 = [P("A.2 Sampling weights and design", "h2"),
          P("Each participant's sampling weight is the number of people in the target population that he or she represents, "
            "after accounting for unequal selection probabilities and nonresponse. A participant from an oversampled group "
            "has a smaller weight than one from an undersampled group, so groups can be contributed to the sample in proportions "
            "that differ from the population. Because HbA1c is measured in blood, we use the phlebotomy weight <b>WTPH2YR</b> "
            "(as stated in the GHB_L documentation); the examination weight WTMEC2YR is shown for comparison. The weights vary "
            "by a factor of 55, giving a design effect from weighting of about 1.55 and an effective sample size of about 3,550, "
            "i.e., weighted estimates are less precise than the nominal sample size suggests. The design variables SDMVSTRA and "
            "SDMVPSU will be used for variance estimation in later phases.")]
    w_t = wsum.set_index("weight").T
    w_rows = [["Minimum", f"{w_t.loc['min','WTPH2YR']:,.0f}", f"{w_t.loc['min','WTMEC2YR']:,.0f}"],
              ["Median", f"{w_t.loc['median','WTPH2YR']:,.0f}", f"{w_t.loc['median','WTMEC2YR']:,.0f}"],
              ["Maximum", f"{w_t.loc['max','WTPH2YR']:,.0f}", f"{w_t.loc['max','WTMEC2YR']:,.0f}"],
              ["Maximum / minimum", f"{w_t.loc['max_to_min_ratio','WTPH2YR']:.1f}", f"{w_t.loc['max_to_min_ratio','WTMEC2YR']:.1f}"],
              ["Sum of weights (millions)", f"{w_t.loc['sum_millions','WTPH2YR']:.1f}", f"{w_t.loc['sum_millions','WTMEC2YR']:.1f}"],
              ["Coefficient of variation", f"{w_t.loc['cv','WTPH2YR']:.2f}", f"{w_t.loc['cv','WTMEC2YR']:.2f}"],
              ["Kish design effect (1 + CV^2)", f"{w_t.loc['kish_design_effect','WTPH2YR']:.2f}", f"{w_t.loc['kish_design_effect','WTMEC2YR']:.2f}"],
              ["Effective sample size", f"{w_t.loc['effective_n','WTPH2YR']:,.0f}", f"{w_t.loc['effective_n','WTMEC2YR']:,.0f}"]]
    S += A2 + make_table(w_rows, ["Statistic", "WTPH2YR", "WTMEC2YR"], [2.8, 1.4, 1.4],
                         f"Summary of sampling weights in the analytic sample (n = {n_final:,}).")
    wg_rows = [[CAT_NAMES.get(r.variable, r.variable), r.group, f"{r.n:,}", f"{r.mean_weight:,.0f}",
                f"{r.population_millions:.1f}", f"{r.pct_of_sample:.1f}", f"{r.pct_of_population:.1f}"]
               for r in wg.itertuples()]
    S += make_table(wg_rows, ["Variable", "Group", "n", "Mean weight", "Population (millions)", "% of sample", "% of population"],
                    [1.4, 1.7, 0.6, 0.9, 1.0, 0.8, 0.9],
                    "Average weight (adults represented per participant) and share of sample versus weighted population, by group.")
    S += [P("Adults aged 60 or older have the smallest weights (average 28,700 adults per participant versus 59,700 among those "
            "aged 20-39), which is what the age oversampling implies. Differences by race and Hispanic origin are small, "
            "consistent with the absence of oversampling on these characteristics in this cycle.")]

    S += [P("A.3 Unweighted versus weighted summaries", "h2"),
          P(f"Table 13 compares unweighted and weighted summaries. Age shows the largest difference: the unweighted mean is "
            f"{rvw.loc['RIDAGEYR','raw_mean']:.1f} years and the weighted mean {rvw.loc['RIDAGEYR','weighted_mean']:.1f} years, "
            f"because the sample overrepresents older adults (Figure 7). The weighted prevalence of diagnosed diabetes is "
            f"{diab['weighted_pct']:.1f}% compared with {diab['raw_pct']:.1f}% in the sample. In contrast, the mean HbA1c "
            f"({rvw.loc['LBXGH','raw_mean']:.2f} vs {rvw.loc['LBXGH','weighted_mean']:.2f}%), BMI "
            f"({rvw.loc['BMXBMI','raw_mean']:.2f} vs {rvw.loc['BMXBMI','weighted_mean']:.2f}), and sleep duration "
            f"({rvw.loc['sleep_hours','raw_mean']:.2f} vs {rvw.loc['sleep_hours','weighted_mean']:.2f} h) change very little. "
            "The unweighted description is therefore a reasonable summary of these outcomes but not of the age composition or "
            "the prevalence of diabetes; weights will be used for all population-level estimates.")]
    rn_rows = [[VAR_NAMES.get(r.Index, r.Index), f"{r.raw_mean:.2f}", f"{r.weighted_mean:.2f}", f"{r.raw_median:.2f}",
                f"{r.weighted_median:.2f}", f"{r.raw_sd:.2f}", f"{r.weighted_sd:.2f}"] for r in rvw.itertuples()]
    S += make_table(rn_rows, ["Variable", "Raw mean", "Weighted mean", "Raw median", "Weighted median", "Raw SD", "Weighted SD"],
                    [1.9, 0.8, 0.95, 0.85, 1.05, 0.7, 0.9],
                    "Quantitative variables: unweighted versus weighted (WTPH2YR) summaries. Weighted median = smallest value whose "
                    "cumulative weight share reaches 50%; weighted SD uses the weights as frequency weights (no design-based variance).")
    rc_rows = [[CAT_NAMES.get(r.variable, r.variable), r.category, f"{r.raw_pct:.1f}", f"{r.weighted_pct:.1f}", f"{r.difference_pp:+.1f}"]
               for r in cat.itertuples()]
    S += make_table(rc_rows, ["Variable", "Category", "Sample %", "Weighted %", "Difference (pp)"], [1.6, 2.4, 0.9, 1.0, 1.1],
                    "Categorical variables: unweighted versus weighted percentages.")
    S += [figure("fig7_age_raw_vs_weighted.png",
                 "Age distribution in the analytic sample (unweighted) and in the weighted population. Older adults are "
                 "overrepresented in the sample.", width=4.4)]

    A4 = [P("A.4 Analytic population", "h2"),
          P(f"The analytic population consists of adults aged 20 years or older who were examined in the MEC, were not pregnant, "
            f"and had non-missing HbA1c (with a positive phlebotomy weight), BMI, weekly sleep duration, leisure-time activity, "
            f"and sedentary time. Table 15 reports the number of participants removed at each step; the final sample has "
            f"{n_final:,} adults.")]
    fl_rows = [[r.step, f"{r.n_remaining:,}", f"{r.n_removed:,}"] for r in flow.itertuples()]
    S += A4 + make_table(fl_rows, ["Step (applied sequentially)", "Remaining (n)", "Removed (n)"], [4.0, 1.2, 1.2],
                         "Sample flow from all participants to the analytic sample.")

    # ------------------------------------------------------------------ limitations
    S += [P("Limitations and Next Steps", "h1"),
          P("The main limitations at this stage are: (1) the observational, cross-sectional design; (2) self-reported sleep and "
            "activity, with activity limited to leisure time; (3) complete-case analysis without re-adjustment of the weights; "
            "(4) the age top-code at 80 and the limited information on diet and medication; (5) data collected after the "
            "COVID-19 pandemic, which may have changed sleep and activity patterns; and (6) descriptive summaries that do not yet "
            "account for the complex design in the variance. Phase 2 translates these data into probabilities and distributions "
            "(conditional probabilities, binomial and normal models), Phase 3 adds design-aware estimation and tests, Phase 4 "
            "fits regression models, and Phase 5 repeats the main analysis under alternative definitions, including without "
            "the flagged observations and without adults with diagnosed diabetes.")]

    S += [P("Reproducibility", "h1"),
          P("All tables and figures in this report are produced by the scripts in <font face='Courier'>src/</font> "
            "(<font face='Courier'>01_load_merge.py</font> to <font face='Courier'>06_build_report.py</font>) from the six "
            "public NHANES files listed in <font face='Courier'>data/README.md</font>. Raw data are not stored in the repository.")]
    return S


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUT_PATH), pagesize=letter, leftMargin=0.85 * inch, rightMargin=0.85 * inch,
        topMargin=0.8 * inch, bottomMargin=0.85 * inch,
        title="Phase 1 Report - NHANES 2021-2023: Sleep, Physical Activity, and HbA1c",
    )
    story = build_story(load())
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"Report written to {OUT_PATH}")


if __name__ == "__main__":
    main()
