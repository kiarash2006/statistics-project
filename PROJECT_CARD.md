# Project Card

## Repositories:

- GitHub : https://github.com/kiarash2006/statistics-project.git
- Hamgit : https://hamgit.ir/kiarash.hajizadeh.06/statistics.git

## 1. Dataset and subset

- Track: A (NHANES August 2021–August 2023, National Center for Health Statistics, CDC).
- Files used: DEMO_L (demographics, sampling weights, design variables), GHB_L (glycohemoglobin and phlebotomy weight), SLQ_L (sleep), PAQ_L (physical activity), BMX_L (body measures), DIQ_L (diabetes questionnaire).
- Merge key: SEQN (participant identifier).
- Initial scope: adults aged 20 years or older who were examined in the mobile examination center, excluding pregnant women, with complete data on HbA1c, BMI, sleep, and physical activity.

## 2. Working title

Sleep Duration, Physical Activity, and Glycated Hemoglobin Among U.S. Adults: An Analysis of NHANES 2021–2023

## 3. Main statistical question

Among U.S. civilian noninstitutionalized adults aged 20 years or older, are habitual sleep duration and leisure-time physical activity associated with HbA1c, and does this association change after accounting for age, sex, and body mass index (BMI)?

A secondary question examines how sleep duration and physical activity are associated with BMI.

## 4. Unit of observation and target population

- Unit of observation: one participant (one row per SEQN). There are no repeated measurements per person.
- Target population: the U.S. civilian noninstitutionalized population aged 20 years or older. Results are interpreted for this population only through the sampling weights (WTPH2YR); unweighted results describe the analytic sample.

## 5. Main variables and measurement scales

| Variable | Description | Type |
|---|---|---|
| LBXGH | HbA1c (%) | Quantitative, continuous |
| BMXBMI | Body mass index (kg/m²) | Quantitative, continuous |
| sleep_hours | Weekly average sleep (5 × workday + 2 × non-workday) / 7 | Quantitative, continuous (derived) |
| mvpa_min_week | Leisure-time moderate + vigorous activity (min/week) | Quantitative, continuous, right-skewed (derived) |
| sedentary_hours | Usual daily sitting time (hours) | Quantitative, continuous |
| RIDAGEYR | Age (years; top-coded at 80) | Quantitative, discrete |
| RIAGENDR | Sex | Nominal, binary |
| RIDRETH3 | Race and Hispanic origin | Nominal |
| DIQ010 | Diagnosed diabetes (yes / no / borderline) | Nominal |
| sleep_cat, mvpa_cat, bmi_cat | Categorized sleep, activity, BMI | Ordinal (derived) |
| WTPH2YR, SDMVSTRA, SDMVPSU | Phlebotomy weight, masked stratum, masked PSU | Design variables |

## 6. Roles of the variables

- Response: HbA1c (primary); BMI (secondary).
- Explanatory: sleep duration, leisure-time physical activity, and sedentary time.
- Adjustment variables: age, sex, race and Hispanic origin; BMI when HbA1c is the response.
- Grouping variables: sleep, activity, and BMI categories (descriptive and ANOVA comparisons); diagnosed diabetes (stratification and sensitivity analysis).

## 7. Type of question

Associational, with descriptive and comparative components. No causal claim is made.

## 8. Initial hypothesis

Based on prior epidemiological reasoning, and specified before any inferential analysis: (a) mean HbA1c is higher among adults with short (<7 h) or long (≥9 h) sleep than among adults sleeping 7 to <9 h; (b) higher leisure-time physical activity is associated with lower mean HbA1c; and (c) part of these associations is accounted for by BMI. Descriptive summaries produced in Phase 1 were inspected, but no inference was performed. The exact null and alternative hypotheses will be formalized in Phase 3.

## 9. Initial limitations

1. Observational, cross-sectional data: associations cannot establish causation, and reverse causation and residual confounding (diet, medications, shift work) are possible.
2. Self-reported exposures: sleep and physical activity are self-reported, and only leisure-time activity is measured.
3. Complex survey design: unweighted summaries describe the sample; adults aged 60+ were oversampled. Design-based variance estimation will be added in later phases.
4. Missing data: a complete-case analytic sample (n = 5,490 of 6,023 eligible adults) is used, and weights were not re-adjusted for item nonresponse.
5. HbA1c measurement context: HbA1c is affected by diabetes treatment (14.0% of the sample report diagnosed diabetes) and by other conditions.
6. Timing: data were collected after the COVID-19 pandemic, which may have altered sleep and activity patterns.