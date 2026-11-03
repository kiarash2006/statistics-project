# Sleep, Physical Activity, and HbA1c Among U.S. Adults (NHANES 2021–2023)

Course project for the Statistics course (Fall 1405), Track A.
See PROJECT_CARD.md for the statistical question and design, and data/README.md for data sources.

## Repository structure

- PROJECT_CARD.md: statistical framework of the project
- data/: data documentation (raw and processed files are not tracked)
- src/: analysis scripts, run in numeric order
- figures/: figures by phase
- reports/: tables and reports by phase

## Reproducing Phase 1

1. Install the requirements: pip install -r requirements.txt
2. Place the six NHANES .xpt files in data/raw/ (see data/README.md).
3. Run, in order: 01_load_merge.py, 02_build_analytic_dataset.py, 03_quality_and_descriptives.py, 04_weights_and_weighted_summaries.py, 05_figures_and_group_comparison.py, 06_build_report.py.

Tables are written to reports/phase1/tables/, figures to figures/phase1/, and the report to reports/phase1/phase1_report.pdf.

## Status

- Phase 1 (data understanding and descriptive statistics): completed
- Phases 2–5: not started