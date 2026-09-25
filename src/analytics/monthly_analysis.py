from __future__ import annotations
import pandas as pd


def _normalize_monthly_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Support both raw bank CSV files and already-normalized transaction data."""
    data = df.copy()

    rename_map = {
        "Sl. No.": "transaction_id",
        "Transaction Date": "transaction_datetime",
        "Value Date": "value_date",
        "Description": "description",
        "Chq /Ref No.": "reference_no",
        "Amount": "amount",
        "Dr / Cr": "transaction_type",
        "Balance": "balance",
        "Dr / Cr.1": "balance_type",
    }

    for old_name, new_name in rename_map.items():
        if old_name in data.columns and new_name not in data.columns:
            data = data.rename(columns={old_name: new_name})

    if "amount" in data.columns:
        data["amount"] = (
            data["amount"].astype(str).str.replace(",", "", regex=False).str.strip()
        )
        data["amount"] = pd.to_numeric(data["amount"], errors="coerce")

    if "transaction_datetime" in data.columns:
        data["transaction_datetime"] = pd.to_datetime(
            data["transaction_datetime"], errors="coerce")

    if "transaction_type" in data.columns:
        data["transaction_type"] = (
            data["transaction_type"].astype(str).str.strip().str.upper()
        )

    return data


def analyze_monthly_trends(df: pd.DataFrame) -> pd.DataFrame:
    data = _normalize_monthly_dataframe(df)
    required_columns = {"transaction_datetime", "amount", "transaction_type"}
    missing_columns = required_columns - set(data.columns)
    if missing_columns:
        raise ValueError(f"Missing required column: {sorted(missing_columns)}")

    if data.empty:
        return pd.DataFrame(
            columns=[
                "month",
                "transaction_count",
                "credit_count",
                "debit_count",
                "total_income",
                "total_expense",
                "net_cash_flow",
                "average_transaction",
            ]
        )

    data = data.dropna(subset=["transaction_datetime", "amount"]).copy()
    data["amount_abs"] = data["amount"].abs()

    if data.empty:
        return pd.DataFrame(
            columns=[
                "month",
                "transaction_count",
                "credit_count",
                "debit_count",
                "total_income",
                "total_expense",
                "net_cash_flow",
                "average_transaction",
            ]
        )

    monthly = (
        data.assign(month=data["transaction_datetime"].dt.to_period("M"))
        .groupby("month")
        .apply(
            lambda g: pd.Series(
                {
                    "transaction_count": len(g),
                    "credit_count": (g["transaction_type"] == "CR").sum(),
                    "debit_count": (g["transaction_type"] == "DR").sum(),
                    "total_income": g.loc[g["transaction_type"] == "CR", "amount_abs"].sum(),
                    "total_expense": g.loc[g["transaction_type"] == "DR", "amount_abs"].sum(),
                    "average_transaction": g["amount_abs"].mean(),
                }
            )
        )
        .reset_index()
    )

    monthly["net_cash_flow"] = monthly["total_income"] - monthly["total_expense"]
    monthly["month"] = monthly["month"].astype(str)
    monthly = monthly[
        [
            "month",
            "transaction_count",
            "credit_count",
            "debit_count",
            "total_income",
            "total_expense",
            "net_cash_flow",
            "average_transaction",
        ]
    ]

    monetary_columns = ["total_income", "total_expense", "net_cash_flow", "average_transaction"]
    monthly[monetary_columns] = monthly[monetary_columns].round(2)
    return monthly


def get_highest_expense_month(df: pd.DataFrame) -> pd.Series:
    monthly = analyze_monthly_trends(df)
    if monthly.empty:
        return pd.Series(dtype=object)
    return monthly.loc[monthly["total_expense"].idxmax()]


def get_highest_income_month(df: pd.DataFrame) -> pd.Series:
    monthly = analyze_monthly_trends(df)
    if monthly.empty:
        return pd.Series(dtype=object)
    return monthly.loc[monthly["total_income"].idxmax()]


def get_monthly_expense(df: pd.DataFrame) -> pd.DataFrame:
    monthly = analyze_monthly_trends(df)
    return monthly[["month", "total_expense"]].copy()


def get_monthly_income(df: pd.DataFrame) -> pd.DataFrame:
    monthly = analyze_monthly_trends(df)
    return monthly[["month", "total_income"]].copy()

    