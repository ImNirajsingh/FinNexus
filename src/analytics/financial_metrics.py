from __future__ import annotations
from typing import Any
import pandas as pd


def _normalize_transaction_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize raw bank CSV columns to the canonical analysis schema."""
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

    if "transaction_type" in data.columns:
        data["transaction_type"] = (data["transaction_type"].astype(str).str.strip().str.upper())

    if "amount" in data.columns:
        data["amount"] = (data["amount"].astype(str).str.replace(",", "", regex=False).str.strip())
        data["amount"] = pd.to_numeric(data["amount"], errors="coerce")

    if "transaction_datetime" in data.columns:
        data["transaction_datetime"] = pd.to_datetime(
            data["transaction_datetime"], errors="coerce"
        )

    if "counterparty" not in data.columns and "description" in data.columns:
        data["counterparty"] = (
            data["description"]
            .fillna("")
            .astype(str)
            .str.split("/")
            .str[1]
            .fillna("UNKNOWN")
            .str.strip()
            .str.upper()
        )

    return data


def summerize_financials(df: pd.DataFrame) -> dict[str, Any]:
    data = _normalize_transaction_dataframe(df)
    required_columns = {"amount", "transaction_type"}
    missing_columns = required_columns - set(data.columns)
    if missing_columns:
        raise ValueError(f"Missing required column : {sorted(missing_columns)}")

    if data.empty:
        return {
            "total_transactions": 0,
            "credit_transactions": 0,
            "debit_transactions": 0,
            "total_income": 0.0,
            "total_expense": 0.0,
            "net_cash_flow": 0.0,
            "average_transaction": 0.0,
            "median_transaction": 0.0,
            "largest_transaction": 0.0,
            "smallest_transaction": 0.0,
        }

    data = data.dropna(subset=["amount"]).copy()

    data["amount_abs"] = data["amount"].abs()

    credit_mask = data["transaction_type"].eq("CR")
    debit_mask = data["transaction_type"].eq("DR")

    credits = data.loc[credit_mask, "amount_abs"]
    debits = data.loc[debit_mask, "amount_abs"]

    total_transaction = len(data)
    credit_transaction = int(credit_mask.sum())
    debit_transaction = int(debit_mask.sum())

    total_income = float(credits.sum())
    total_expense = float(debits.sum())
    net_cash_flow = total_income - total_expense

    average_transaction = float(data["amount_abs"].mean())
    median_transaction = float(data["amount_abs"].median())
    largest_transaction = float(data["amount_abs"].max())
    smallest_transaction = float(data["amount_abs"].min())

    return {
        "total_transactions": total_transaction,
        "credit_transactions": credit_transaction,
        "debit_transactions": debit_transaction,
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net_cash_flow": round(net_cash_flow, 2),
        "average_transaction": round(average_transaction, 2),
        "median_transaction": round(median_transaction, 2),
        "largest_transaction": round(largest_transaction, 2),
        "smallest_transaction": round(smallest_transaction, 2,)
    }


def get_income_transactions(df: pd.DataFrame) -> pd.DataFrame:
    data = _normalize_transaction_dataframe(df)
    return data[data["transaction_type"].eq("CR")].copy()


def get_expense_transactions(df: pd.DataFrame) -> pd.DataFrame:
    data = _normalize_transaction_dataframe(df)
    return data[data["transaction_type"].eq("DR")].copy()


def get_largest_transactions(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    if n <= 0:
        raise ValueError("n must be greater than 0.")
    result = _normalize_transaction_dataframe(df)
    result["amount_abs"] = result["amount"].abs()
    result = result.dropna(subset=["amount_abs"])
    return result.nlargest(n,"amount_abs")


def get_highest_expenses(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    expenses = get_expense_transactions(df)
    expenses["amount_abs"] = expenses["amount"].abs()
    expenses = expenses.dropna(subset=["amount_abs"])
    return expenses.nlargest(n,"amount_abs")


def get_highest_income(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    income = get_income_transactions(df)
    income["amount_abs"] = income["amount"].abs()
    income = income.dropna(subset=["amount_abs"])
    return income.nlargest(n,"amount_abs")