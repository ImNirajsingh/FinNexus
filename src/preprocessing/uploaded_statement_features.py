from __future__ import annotations
import pandas as pd

def add_uploaded_statement_features(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        raise ValueError("Can't engineer feature on empty statement.")

    data = df.copy()

    data["transaction_datetime"] = pd.to_datetime(data["transaction_datetime"], errors='coerce')
    data["value_date"] = pd.to_datetime(data["value_date"], errors='coerce')
    data["amount"] = pd.to_numeric(data["amount"], errors='coerce')
    data["balance"] = pd.to_numeric(data["balance"], errors='coerce')
    data["transaction_type"] = (data["transaction_type"].astype(str).str.upper().str.strip())

    # Featuring
    data["date"] = data["transaction_datetime"].dt.date
    data["year"] = data["transaction_datetime"].dt.year
    data["month"] = data["transaction_datetime"].dt.month
    data["month_name"] = data["transaction_datetime"].dt.month_name()
    data["day"] = data["transaction_datetime"].dt.day
    data["day_of_week"] = data["transaction_datetime"].dt.day_name()
    data["hour"] = data["transaction_datetime"].dt.hour

    data["amount_abs"] = data["amount"].abs()
    data["signed_amount"] = data["amount_abs"]
    data.loc[data["transaction_type"] == "DR", "signed_amount"] *= -1

    data = data.sort_values("transaction_datetime").reset_index(drop=True)
    data["previous_balance"] = data["balance"].shift(1)

    data["balance_change"] = (data["balance"] - data["previous_balance"])

    data["expected_balance"] = (data["previous_balance"] + data["signed_amount"])

    data["balance_difference"] = (data["balance"] - data["expected_balance"])

    # High value transaction
    threshold = data["amount_abs"].quantile(0.95)
    data["is_high_value"] = (data["amount_abs"] >= threshold)

    # time since prev. trans.
    data["days_since_previous_transaction"] = (
        data["transaction_datetime"].diff().dt.total_seconds().div(86400)
    )

    # Trans. text features
    data["description"] = (data["description"].fillna("").astype(str).str.strip())
    data["description_length"] = data["description"].str.len()
    data["numeric_character_count"] = data["description"].str.count(r"[A-Za-z]")

    # Description features
    try:
        from preprocessing.description_features import add_description_features
        data = add_description_features(data)

    except ImportError:
        data["description_clean"] = data["description"]
        data["payment_mode"] = "UNKNOWN"
        data["counterparty"] = "UNKNOWN"
        data["merchant"] = "UNKNOWN"


    # Final cleanup
    data["amount"] = data["amount"].round(2)
    data["amount_abs"] = data["amount_abs"].round(2)
    data["signed_amount"] = data["signed_amount"].round(2)
    data["balance"] = data["balance"].round(2)
    data["previous_balance"] = data["previous_balance"].round(2)
    data["balance_change"] = data["balance_change"].round(2)
    data["expected_balance"] = data["expected_balance"].round(2)
    data["balance_difference"] = data["balance_difference"].round(2)

    return data