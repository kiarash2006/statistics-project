"""Phase 1 - Step 1: Load the six NHANES 2021-2023 files and merge them on SEQN.

Outputs
-------
data/processed/nhanes_merged.csv       merged participant-level file
reports/phase1/tables/merge_counts.csv  participants per file, before and after merging
"""

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
TABLES_DIR = PROJECT_ROOT / "reports" / "phase1" / "tables"

# DEMO_L is listed first because it is the base file: it contains every
# NHANES participant, so it defines the starting population for the merge.
FILES = ["DEMO_L", "GHB_L", "PAQ_L", "SLQ_L", "BMX_L", "DIQ_L"]


def load_xpt(name: str) -> pd.DataFrame:
    """Read one SAS transport file and make the merge key an integer."""
    df = pd.read_sas(RAW_DIR / f"{name}.xpt", format="xport", encoding="utf-8")
    df["SEQN"] = df["SEQN"].astype(int)
    return df


def build_count_table(tables: dict) -> pd.DataFrame:
    """Count rows and unique participants in each file before merging."""
    demo_ids = set(tables["DEMO_L"]["SEQN"])
    rows = []
    for name, df in tables.items():
        rows.append(
            {
                "file": name,
                "n_rows": len(df),
                "n_unique_seqn": df["SEQN"].nunique(),
                "n_seqn_found_in_demo": df["SEQN"].isin(demo_ids).sum(),
                "n_columns": df.shape[1],
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    tables = {name: load_xpt(name) for name in FILES}

    counts = build_count_table(tables)
    print("Participants per file (before merging):")
    print(counts.to_string(index=False))

    # Left joins keep every participant in DEMO_L. validate="one_to_one"
    # raises an error if SEQN is duplicated in either file, which would
    # silently inflate the row count.
    merged = tables["DEMO_L"]
    for name in FILES[1:]:
        merged = merged.merge(
            tables[name], on="SEQN", how="left", validate="one_to_one"
        )

    assert len(merged) == len(tables["DEMO_L"]), "Row count changed after merging"
    print(f"\nAfter merging: {merged.shape[0]} participants, {merged.shape[1]} columns")

    counts.to_csv(TABLES_DIR / "merge_counts.csv", index=False)
    merged.to_csv(PROCESSED_DIR / "nhanes_merged.csv", index=False)
    print("Saved merged file and count table.")


if __name__ == "__main__":
    main()