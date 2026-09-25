from pathlib import Path
import pandas as pd
from description_features import add_description_features

INPUT_PATH = Path("data/processed/cleaned_transactions.csv")
OUTPUT_PATH = Path("data/processed/transactions_features_v2.csv")

def main():
    print("=" * 70)
    print("UPDATING TRANSACTION FEATURES")
    print("=" * 70)
    print("\nLoading transactions...")
    df = pd.read_csv(INPUT_PATH)

    print(f"Transactions loaded: {len(df):,}")

    print("\nExtracting description features...")

    df = add_description_features(df)

    print("\nFeature extraction completed.")

    print("\nNew / updated columns:")

    for column in [
        "description_clean",
        "payment_mode",
        "counterparty",
        "merchant",
    ]:
        print(f"  - {column}")

    print("\nSaving updated dataset...")

    df.to_csv(OUTPUT_PATH, index=False)

    print(f"\nSaved to: {OUTPUT_PATH}")
    print(f"Rows: {len(df):,}")

    print("\nSample results:")
    print(
        df[
            [
                "transaction_id",
                "description",
                "payment_mode",
                "counterparty",
                "merchant",
            ]
        ].head(10).to_string(index=False)
    )

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()