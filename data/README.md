# Data

## Source

NHANES August 2021–August 2023, National Center for Health Statistics (NCHS), Centers for Disease Control and Prevention (CDC).

- Cycle page: https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?Cycle=2021-2023
- Date downloaded: [11/1/2026]

## Files

| File | Content | Documentation |
|---|---|---|
| DEMO_L.xpt | Demographics, sampling weights, design variables | https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DEMO_L.htm |
| GHB_L.xpt | Glycohemoglobin (HbA1c), phlebotomy weight | https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/GHB_L.htm |
| SLQ_L.xpt | Sleep disorders questionnaire (sleep duration) | https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/SLQ_L.htm |
| PAQ_L.xpt | Physical activity questionnaire | https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/PAQ_L.htm |
| BMX_L.xpt | Body measures (BMI) | https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BMX_L.htm |
| DIQ_L.xpt | Diabetes questionnaire | https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DIQ_L.htm |

The raw files are not stored in this repository. Download the six .xpt files from the pages above and place them in data/raw/.

## Rebuilding the analytic dataset

Run the scripts in src/ in numeric order:

1. 01_load_merge.py merges the six files on SEQN and writes data/processed/nhanes_merged.csv.
2. 02_build_analytic_dataset.py recodes special codes, derives analysis variables, applies inclusion criteria, and writes data/processed/adults_all.csv and data/processed/analytic_sample.csv.

## Key processing decisions

- Refused (7777) and don't-know (9999) codes are set to missing.
- SAS stores zeros as a tiny positive number (about 5e-79); these are converted to 0 for activity frequencies and sedentary minutes.
- Weekly activity minutes = frequency × occasions per week × minutes per occasion; frequency 0 means 0 minutes.
- Weekly average sleep = (5 × workday sleep + 2 × non-workday sleep) / 7.
- Analytic sample: age ≥ 20, examined, not pregnant, and non-missing HbA1c (with phlebotomy weight > 0), BMI, sleep, activity, and sedentary time (n = 5,490).
- Weight: WTPH2YR, as recommended for analyses using blood analytes.