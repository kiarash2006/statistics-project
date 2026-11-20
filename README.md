# Sleep, Physical Activity, and HbA1c Among U.S. Adults (NHANES 2021–2023)

Course project for the Statistics course (Fall 1405), Track A.
See PROJECT_CARD.md for the statistical question and design, and data/README.md for data sources.

## Repository structure

- PROJECT_CARD.md: statistical framework of the project
- data/: data documentation (raw and processed files are not tracked)
- src/: analysis scripts, run in numeric order
- notebooks/: one walkthrough notebook per phase
- figures/: figures by phase
- reports/: tables and reports by phase

## Reproducing the analysis

1. Install the requirements: pip install -r requirements.txt
2. Place the six NHANES .xpt files in data/raw/ (see data/README.md).
3. Phase 1: run 01_load_merge.py through 06_build_report.py in src/, in order.
4. Phase 2: run 07_probability_events.py, 08_distributions.py, and 09_build_phase2_report.py.

Tables are written to reports/phaseN/tables/, figures to figures/phaseN/, and reports to reports/phaseN/. The notebooks notebooks/phase1_analysis.ipynb and notebooks/phase2_probability.ipynb run these scripts and display the results.

## Status

- Phase 1 (data understanding and descriptive statistics): completed
- Phase 2 (probability and distributions): completed
- Phases 3–5: not started