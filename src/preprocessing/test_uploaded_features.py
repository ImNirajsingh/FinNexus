from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from ingestion.statement_loader import (
    load_statement,
    normalize_statement,
)

from preprocessing.uploaded_statement_features import (
    add_uploaded_statement_features,
)


DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "bank_statement.csv"
)

FALLBACK_DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "AccountStatement_18-Sep-2025_18-Sep-2026.csv"
)


def resolve_data_file() -> Path:
    """Use the real sample statement when the raw placeholder file is still checked in."""
    if DATA_FILE.exists():
        try:
            preview = DATA_FILE.read_text(encoding="utf-8", errors="ignore").strip()
        except OSError:
            preview = ""

        if preview and not preview.startswith("# Placeholder:"):
            return DATA_FILE

    if FALLBACK_DATA_FILE.exists():
        return FALLBACK_DATA_FILE

    raise FileNotFoundError(
        "No valid bank statement CSV was found in data/raw/bank_statement.csv "
        "or the sample file under data/."
    )


def main():

    print("=" * 70)
    print("UPLOADED STATEMENT FEATURE TEST")
    print("=" * 70)

    source_file = resolve_data_file()
    print(f"\nUsing source file: {source_file}")

    # Load existing test statement through the project loader so malformed bank
    # export rows are repaired before normalization runs.
    raw_df = load_statement(source_file)

    print(f"\nRaw rows: {len(raw_df):,}")

    # Normalize
    normalized_df, warnings = normalize_statement(raw_df)

    print(
        f"Normalized rows: "
        f"{len(normalized_df):,}"
    )

    # Feature engineering
    features_df = add_uploaded_statement_features(
        normalized_df
    )

    print(
        f"Feature-engineered rows: "
        f"{len(features_df):,}"
    )

    print("\nColumns:")
    for column in features_df.columns:
        print(f"  - {column}")

    print("\nSample:")
    print(
        features_df[
            [
                "transaction_id",
                "transaction_datetime",
                "amount",
                "transaction_type",
                "signed_amount",
                "payment_mode",
                "counterparty",
                "merchant",
                "days_since_previous_transaction",
            ]
        ].head(5).to_string(index=False)
    )

    print("\nTransaction type counts:")
    print(
        features_df["transaction_type"]
        .value_counts()
        .to_string()
    )

    print("\nFeature test completed successfully.")


if __name__ == "__main__":
    main()