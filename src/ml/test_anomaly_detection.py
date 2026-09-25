import pandas as pd

from anomaly_detection import (
    detect_anomalies,
    get_anomalous_transactions,
)


# --------------------------------------------------
# Load data
# --------------------------------------------------

DATA_PATH = "data/processed/cleaned_transactions.csv"

print("Loading transactions...")

df = pd.read_csv(DATA_PATH)

print(f"Total transactions: {len(df):,}")


# --------------------------------------------------
# Detect anomalies
# --------------------------------------------------

print("Running anomaly detection...")

result = detect_anomalies(
    df,
    contamination=0.02,
    random_state=42,
)


# --------------------------------------------------
# Results
# --------------------------------------------------

total_anomalies = result["is_anomaly"].sum()

print()
print("=" * 70)
print("ANOMALY DETECTION")
print("=" * 70)

print(f"Total transactions : {len(result):,}")
print(f"Anomalies detected  : {total_anomalies:,}")
print(
    f"Anomaly percentage  : "
    f"{total_anomalies / len(result) * 100:.2f}%"
)


# --------------------------------------------------
# Show most anomalous transactions
# --------------------------------------------------

anomalies = get_anomalous_transactions(
    result,
    n=20,
)

print()
print("TOP ANOMALOUS TRANSACTIONS")
print("=" * 70)

columns = [
    "transaction_id",
    "transaction_datetime",
    "amount",
    "transaction_type",
    "counterparty",
    "transaction_category",
    "anomaly_score",
]

available_columns = [
    column
    for column in columns
    if column in anomalies.columns
]

print(
    anomalies[available_columns]
    .to_string(index=False)
)


# --------------------------------------------------
# Save results
# --------------------------------------------------

OUTPUT_PATH = "data/processed/anomaly_detection.csv"

result.to_csv(
    OUTPUT_PATH,
    index=False
)

print()
print(f"Saved results to: {OUTPUT_PATH}")