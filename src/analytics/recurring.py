from __future__ import annotations
import pandas as pd

def detect_recurring_transaction(df: pd.DataFrame, min_occurrences: int = 3, amount_tolerance: int = 0.10, 
                                 interval_tolerance_days: int = 7) -> pd.DataFrame:
    data = df.copy()
    if "transaction_datetime" not in data.columns and "transaction_date" in data.columns:
        data["transaction_datetime"] = data["transaction_date"]
    if "counterparty" not in data.columns and "description_clean" in data.columns:
        data["counterparty"] = (
            data["description_clean"].fillna("").astype(str).str.split("/").str[1]
        )

    required_column = {"transaction_datetime", "amount", "transaction_type", "counterparty"}
    missing_column = required_column - set(data.columns)
    if missing_column:
        raise ValueError(f"Missing required column : {sorted(missing_column)}")
    if min_occurrences < 2:
        raise ValueError("min_occurrences must be at 2.")
    if interval_tolerance_days < 0:
        raise ValueError("interval_tolerance_days can't be negative.")
    if data.empty:
        return pd.DataFrame()

    data["transaction_datetime"] = pd.to_datetime(data["transaction_datetime"], errors='coerce')
    data["amount"] = (data["amount"].astype(str).str.replace(",", "", regex=False).str.strip())
    data["amount"] = pd.to_numeric(data["amount"], errors='coerce')
    data["transaction_value"] = data["amount"].abs()
    data["counterparty"] = (data["counterparty"].astype(str).str.strip().str.upper())

    data = data.dropna(subset=["transaction_datetime", "transaction_value"])
    data = data[
        ~data["counterparty"].isin(
            [
                "",
                "UNKNOWN",
                "NAN",
                "NONE",
            ]
        )
    ]

    if data.empty:
        return pd.DataFrame()

    data = data.sort_values(["counterparty", "transaction_type", "transaction_datetime"])
    results= []

    grouped = data.groupby(["counterparty", "transaction_type"])

    for(counterparty, transaction_type), group in grouped:
        if len(group) < min_occurrences:
            continue
        group = group.sort_values("transaction_datetime").copy()
        amounts = group["transaction_value"]
        median_amount = amounts.median()

        if median_amount == 0 :
            continue

        amount_deviation = ((amounts - median_amount).abs() / median_amount)
        amount_consistent = (amount_deviation <= amount_tolerance)
        amount_consistency_ratio = (amount_consistent.mean())

        if amount_consistency_ratio < 0.60:
            continue

        intervals = (group["transaction_datetime"].diff().dt.total_seconds() / 86400)
        intervals = intervals.dropna()
        if intervals.empty:
            continue

        median_interval = intervals.median()
        interval_deviation = ((intervals - median_interval).abs())
        consistent_interval = (interval_deviation <= interval_tolerance_days)
        interval_consistency_ratio = (consistent_interval.mean())

        if interval_consistency_ratio < 0.50:
            continue

        if 5 <= median_interval <= 9:
            frequency = "WEEKLY"

        elif 12 <= median_interval <= 17:
            frequency = "BIWEEKLY"

        elif 25 <= median_interval <= 35:
            frequency = "MONTHLY"

        elif 80 <= median_interval <= 100:
            frequency = "QUARTERLY"

        else:
        # Ignore irregular/frequent transactions
        # such as daily person-to-person payments.
            continue



        # if 5 <= median_interval <= 9:
        #     frequency = "WEEKLY"
        # elif 12 <= median_interval <= 17:
        #     frequency = "BIWEEKLY"
        # elif 25 <= median_interval <= 35:
        #     frequency = "MONTHLY"
        # elif 80 <= median_interval <= 100:
        #     frequency = "QUARTERLY"
        # else :
        #     frequency = "OTHER"

        results.append(
            {
                "counterparty" : counterparty,
                "transaction_type" : transaction_type,
                "occurrences" : len(group),
                "average_amount" : round(amounts.mean(), 2),

                "median_amount" : round(median_amount, 2),
                "minimum_amount" : round(amounts.min(), 2),
                "maximum_amount" : round(amounts.max(), 2),
                "median_interval_days" : round(median_interval, 1),
                "frequency" : frequency,
                "amount_consistency" : round(amount_consistency_ratio * 100, 2),
                "interval_consistency" : round(interval_consistency_ratio * 100, 2),
                "first_transaction" : (group["transaction_datetime"].min()),
                "last_transaction" : (group["transaction_datetime"].max())
            }
        )

    if not results:
        return pd.DataFrame(
            columns=[
                "counterparty",
                "transaction_type",
                "occurrences",
                "average_amount",
                "median_amount",
                "minimum_amount",
                "maximum_amount",
                "median_interval_days",
                "frequency",
                "amount_consistency",
                "interval_consistency",
                "first_transaction",
                "last_transaction",
            ]
        )

    recurring = pd.DataFrame(results)

    recurring = recurring.sort_values(
        [
            "occurrences",
            "amount_consistency"
        ],
        ascending=[
            False,
            False
        ]
    ).reset_index(drop=True)
    return recurring