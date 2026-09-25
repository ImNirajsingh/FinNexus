from __future__ import annotations
import pandas as pd

def analyze_categories(df: pd.DataFrame) ->pd.DataFrame:
    data = df.copy()
    if "transaction_category" not in data.columns and "transaction_class" in data.columns:
        data["transaction_category"] = data["transaction_class"]

    required_column = {"transaction_category", "amount", "transaction_type"}
    missing_column = required_column - set(data.columns)
    if missing_column:
        raise ValueError(f"Missing required column : {sorted(missing_column)}")
    if df.empty:
        return pd.DataFrame(
            columns=[
                "category",
                "transaction_count",
                "credit_count",
                "debit_count",
                "total_income",
                "total_expense",
                "net_cash_flow",
                "average_transaction",
                "expense_percentage",
            ]
        )
    data["amount"] = (data["amount"].astype(str).str.replace(",", "", regex=False).str.strip())
    data["amount"] = pd.to_numeric(data["amount"], errors='coerce')
    data["transaction_type"] = (data["transaction_type"].astype(str).str.strip().str.upper())
    data["transaction_category"] = (data["transaction_category"].astype(str).str.strip())
    data["transaction_category"] = (data["transaction_category"].replace(
        {

         "" : "UNKNOWN",
         "nan" : "UNKNOWN",
         "None" : "UNKNOWN"

        }
    ))

    data = data.dropna(subset=["amount"])
    if data.empty:
        return pd.DataFrame()
    data["transaction_value"] = data["amount"].abs()

    data["income_amount"] = data["transaction_value"].where(data["transaction_type"] == "CR",0,)

    data["expense_amount"] = data["transaction_value"].where(data["transaction_type"] == "DR",0,)

    # data["income_amount"] = data["amount"].where(data["transaction_type"] == "CR", 0)
    # data["expense_amount"] = data["amount"].where(data["transaction_type"] == "DR", 0)

    # category_summary = (data.groupby("transaction_category").agg(transaction_count = ("amount", "count"),
    #                                                              credit_count = ("transaction_type", lambda x: (x == "CR").sum(),),
    #                                                              debit_count = ("transaction_type", lambda x: (x == "DR").sum(),),
    #                                                              total_income = ("income_amount", "sum"),
    #                                                              total_expense = ("expense_amount", "sum"),
    #                                                              average_transaction = ("amount", "mean"),
    #                                                              ).reset_index()
    #                                                              )

    category_summary = (
        data.groupby("transaction_category").agg(transaction_count=("transaction_value", "count"),
            credit_count=(
                "transaction_type",
                lambda x: (x == "CR").sum(),
            ),

            debit_count=(
                "transaction_type",
                lambda x: (x == "DR").sum(),
            ),

            total_income=("income_amount", "sum"),

            total_expense=("expense_amount", "sum"),

            average_transaction=("transaction_value", "mean"),
        )
        .reset_index()
    )


    category_summary = category_summary.rename(columns={"transaction_category" : "category"})
    category_summary["net_cash_flow"] = category_summary["total_income"] - category_summary["total_expense"]


    total_expense = category_summary["total_expense"].sum()
    if total_expense > 0:
        category_summary["expense_percentage"] = (category_summary["total_expense"] / total_expense * 100)
    else:
        category_summary["expense_percentage"] = 0.0

    category_summary = category_summary[
        [
            "category",
            "transaction_count",
            "credit_count",
            "debit_count",
            "total_income",
            "total_expense",
            "net_cash_flow",
            "average_transaction",
            "expense_percentage",
        ]
    ]

    monetary_column = [
        "total_income",
        "total_expense",
        "net_cash_flow",
        "average_transaction",
    ]

    category_summary[monetary_column] = (category_summary[monetary_column].round(2))
    category_summary["expense_percentage"] = (category_summary["expense_percentage"].round(2))
    category_summary = category_summary.sort_values(by="total_expense", ascending=False,).reset_index(drop=True)
    return category_summary


def get_top_expense_category(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    if n <= 0:
        raise ValueError("n must me greater than 0.")
    categories = analyze_categories(df)
    return categories.head(n).copy()


def get_top_income_category(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    if n <= 0:
        raise ValueError("n must be greater than 0.")
    categories = analyze_categories(df)
    return (categories.sort_values(by="total_income", ascending=False).head(n).reset_index(drop=True))


def get_category_transaction(df: pd.DataFrame, category: str) -> pd.DataFrame:
    if "transaction_category" not in df.columns:
        raise ValueError("Missing required column : transaction_column")
    return df[df["transaction_category"].astype(str).str.strip().str.casefold().eq(category.strip().casefold())].copy()