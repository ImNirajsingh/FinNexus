from pathlib import Path
import sys
import pandas as pd
import re

SRC_DIR = Path(__file__).resolve().parents[1]

if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

try:
    from src.graph.query_router import QueryRoute, route_query
    from src.llm.response_generator import generate_financial_response
    from src.analytics.financial_metrics import summerize_financials
    from src.analytics.monthly_analysis import analyze_monthly_trends
    from src.analytics.category_analysis import analyze_categories
    from src.ml.anomaly_detection import detect_anomalies, get_anomalous_transactions
    from src.rag.retriever import search_transactions
    from src.rag.uploaded_retriever import search_uploaded_transactions
    from src.rag.uploaded_retriever import search_uploaded_vectorstore
except ImportError:  # pragma: no cover
    from query_router import QueryRoute, route_query
    from llm.response_generator import generate_financial_response
    from analytics.financial_metrics import summerize_financials
    from analytics.monthly_analysis import analyze_monthly_trends
    from analytics.category_analysis import analyze_categories
    from ml.anomaly_detection import detect_anomalies, get_anomalous_transactions
    from rag.retriever import search_transactions
    from rag.uploaded_retriever import search_uploaded_transactions
    from rag.uploaded_retriever import search_uploaded_vectorstore


# Legacy fallback dataset
# This is kept only for backward compatibility/testing.
# The Streamlit application will pass the uploaded dataframe.

DATA_PATH = (Path(__file__).resolve().parents[2]
    / "data"
    / "processed"
    / "transactions_features_v2.csv"
)
# Month extraction
def extract_month_from_query(query: str):
    """Extract month name and optional year from a user query."""
    months = {
        "january": 1,
        "jan": 1,
        "february": 2,
        "feb": 2,
        "march": 3,
        "mar": 3,
        "april": 4,
        "apr": 4,
        "may": 5,
        "june": 6,
        "jun": 6,
        "july": 7,
        "jul": 7,
        "august": 8,
        "aug": 8,
        "september": 9,
        "sept": 9,
        "sep": 9,
        "october": 10,
        "oct": 10,
        "november": 11,
        "nov": 11,
        "december": 12,
        "dec": 12,
    }
    q = query.lower()
    for month_name, month_number in months.items():
        if re.search(rf"\b{month_name}\b", q):
            year_match = re.search(r"\b(20\d{2})\b", q)

            year = (int(year_match.group(1))
                if year_match
                else None
            )
            return month_name, month_number, year
        
    return None, None, None

# Load transaction dataframe
def load_transaction():
    data = pd.read_csv(DATA_PATH)
    data = data.rename(
        columns={
            "transaction_date": "transaction_datetime",
            "description_raw": "description",
        }
    )

    if "transaction_category" not in data.columns:
        data["transaction_category"] = data.get("transaction_class", "UNKNOWN")

    data["transaction_category"] = (data["transaction_category"].fillna("UNKNOWN"))

    return data


def _get_dataframe(df: pd.DataFrame | None) -> pd.DataFrame:

    if df is not None:
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame.")

        if df.empty:
            raise ValueError("The provided transaction dataframe is empty.")

        return df.copy()
    return load_transaction()


# Exact transaction / counterparty matching
def _normalize_match_text(value) -> str:

    if value is None:
        return ""
    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _extract_transaction_target(query: str):
    
    q = query.strip()
    match = re.search(r"\b(?:to|on|at|from|with)\s+(.+)$", q, flags=re.IGNORECASE)
    if not match:
        return None
    
    target = match.group(1).strip(" \t\r\n\"'`?!.,;:")

    target = re.sub(
        r"\s+(?:in|during|for)\s+"
        r"(?:january|february|march|april|may|june|july|august|"
        r"september|october|november|december|jan|feb|mar|apr|jun|"
        r"jul|aug|sep|sept|oct|nov|dec|\d{4})"
        r"(?:\s+20\d{2})?\s*$",
        "", target, flags=re.IGNORECASE,
    )

    target = re.sub(r"\s+", " ", target).strip(" \t\r\n\"'`?!.,;:")
    target = re.sub(r"\s+(?:please|can you|could you|give me|show me)$", "", target, flags=re.IGNORECASE).strip()
    return target or None


def _is_exact_transaction_amount_query(query: str) -> bool:
    q = query.lower().strip()
    amount_intent = ("how much" in q or "how many" in q or "total amount" in q or "total" in q)
    transaction_intent = any(phrase in q
        for phrase in ("send", "sent", "spend", "spent", "paid", "payment", "transfer", "transferred",)
    )

    return amount_intent and transaction_intent and bool(_extract_transaction_target(query))


def _execute_exact_transaction_query(query: str, data: pd.DataFrame):
    target = _extract_transaction_target(query)
    if not target:
        return None

    work = data.copy()
    if "transaction_datetime" in work.columns:
        work["transaction_datetime"] = pd.to_datetime(work["transaction_datetime"], errors="coerce")

    if "amount" not in work.columns:
        return None

    work["amount_numeric"] = pd.to_numeric(work["amount"], errors="coerce")
    work["amount_abs"] = work["amount_numeric"].abs()

    target_norm = _normalize_match_text(target).strip("/")
    counterparty_text = work.get("counterparty", pd.Series("", index=work.index)).fillna("").map(_normalize_match_text)
    description_text = work.get("description", pd.Series("", index=work.index)).fillna("").map(_normalize_match_text)
    target_mask = (counterparty_text.str.contains(re.escape(target_norm), na=False)| 
                   description_text.str.contains(re.escape(target_norm), na=False))

    if "/" in target_norm:
        parts = [part.strip() for part in target_norm.split("/") if part.strip()]
        if parts:
            target_name = parts[-1]
            target_mask = target_mask | (counterparty_text.str.contains(re.escape(target_name), na=False)
                | description_text.str.contains(re.escape(target_name), na=False)
            )

    work = work.loc[target_mask].copy()
    if work.empty:
        return {
            "route": QueryRoute.ANALYTICS.value,
            "query": query,
            "exact_transaction_query": True,
            "target": target,
            "transaction_count": 0,
            "total_amount": 0.0,
            "transactions": [],
            "message": f"No transactions were found matching '{target}' in the uploaded statement.",
        }

    q = query.lower()
    if any(
        phrase in q
        for phrase in ("sent", "send", "spend", "spent", "paid", "payment", "transfer", "transferred")
    ):
        direction = "DR"
        direction_name = "debit"
    elif "received" in q or "income" in q:
        direction = "CR"
        direction_name = "credit"
    else:
        direction = None
        direction_name = "transaction"

    if direction is not None and "transaction_type" in work.columns:
        work["transaction_type"] = (work["transaction_type"].astype(str).str.upper().str.strip())
        work = work.loc[work["transaction_type"] == direction].copy()

    month_name, month_number, requested_year = extract_month_from_query(query)
    if "transaction_datetime" in work.columns:
        if month_number is not None:
            work = work.loc[work["transaction_datetime"].dt.month == month_number].copy()

            if requested_year is not None:
                work = work.loc[work["transaction_datetime"].dt.year == requested_year].copy()

        else:
            year_match = re.search(r"\b(20\d{2})\b", query)
            if year_match:
                requested_year = int(year_match.group(1))
                work = work.loc[work["transaction_datetime"].dt.year == requested_year].copy()

    if work.empty:
        period_text = ""
        if month_name and requested_year:
            period_text = f" in {month_name.title()} {requested_year}"
        elif month_name:
            period_text = f" in {month_name.title()}"
        elif requested_year:
            period_text = f" in {requested_year}"
        return {
            "route": QueryRoute.ANALYTICS.value,
            "query": query,
            "exact_transaction_query": True,
            "target": target,
            "direction": direction_name,
            "transaction_count": 0,
            "total_amount": 0.0,
            "transactions": [],
            "message": f"No {direction_name} transactions matching '{target}'{period_text} were found in the uploaded statement.",
        }

    total_amount = round(float(work["amount_abs"].sum()), 2)
    transaction_records = []
    for _, row in work.sort_values("transaction_datetime", na_position="last").iterrows():
        transaction_records.append({
            "transaction_id": str(row.get("transaction_id", "")),
            "date": str(row.get("transaction_datetime", "")),
            "amount": round(float(row["amount_abs"]), 2),
            "transaction_type": str(row.get("transaction_type", "")),
            "counterparty": str(row.get("counterparty", "UNKNOWN")),
            "payment_mode": str(row.get("payment_mode", "UNKNOWN")),
            "description": str(row.get("description", "")),
            "reference_no": str(row.get("reference_no", "")),
        })

    return {
        "route": QueryRoute.ANALYTICS.value,
        "query": query,
        "exact_transaction_query": True,
        "target": target,
        "direction": direction_name,
        "transaction_count": len(work),
        "total_amount": total_amount,
        "transactions": transaction_records,
    }


def _extract_transaction_search_target(query: str):
    q = query.strip()
    match = re.search(r"\b(?:involving|related to|with|to|from)\s+(.+)$", q, flags=re.IGNORECASE)

    if not match:
        return None

    target = match.group(1).strip(" \t\r\n\"'`?!.,;:")
    target = re.sub(
        r"\s+(?:in|during|for)\s+"
        r"(?:january|february|march|april|may|june|july|august|"
        r"september|october|november|december|jan|feb|mar|apr|jun|"
        r"jul|aug|sep|sept|oct|nov|dec|\d{4})"
        r"(?:\s+20\d{2})?\s*$",
        "", target, flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", target).strip(" \t\r\n\"'`?!.,;:") or None


def _execute_exact_transaction_search(query: str, data: pd.DataFrame, limit: int = 20):
    target = _extract_transaction_search_target(query)
    if not target:
        return None

    work = data.copy()
    target_norm = _normalize_match_text(target)
    counterparty_text = work.get("counterparty", pd.Series("", index=work.index)).fillna("").map(_normalize_match_text)
    description_text = work.get("description", pd.Series("", index=work.index)).fillna("").map(_normalize_match_text)

    mask = (counterparty_text.str.contains(re.escape(target_norm), na=False)
        | description_text.str.contains(re.escape(target_norm), na=False))
    
    work = work.loc[mask].copy()

    if "transaction_datetime" in work.columns:
        work["transaction_datetime"] = pd.to_datetime(work["transaction_datetime"], errors="coerce")

    total_matches = len(work)
    if total_matches == 0:
        return {
            "route": QueryRoute.RAG.value,
            "query": query,
            "exact_transaction_search": True,
            "target": target,
            "total_matches": 0,
            "shown_matches": 0,
            "transactions": [],
            "message": f"No transactions were found involving '{target}' in the uploaded statement.",
        }

    work = work.sort_values("transaction_datetime", ascending=False, na_position="last").head(limit)
    transactions = []
    for _, row in work.iterrows():
        transactions.append({
            "transaction_id": str(row.get("transaction_id", "")),
            "date": str(row.get("transaction_datetime", "")),
            "transaction_type": str(row.get("transaction_type", "")),
            "amount": round(float(pd.to_numeric(row.get("amount", 0), errors="coerce") or 0), 2),
            "counterparty": str(row.get("counterparty", "UNKNOWN")),
            "payment_mode": str(row.get("payment_mode", "UNKNOWN")),
            "description": str(row.get("description", "")),
            "reference_no": str(row.get("reference_no", "")),
        })

    shown_matches = len(transactions)
    return {
        "route": QueryRoute.RAG.value,
        "query": query,
        "exact_transaction_search": True,
        "target": target,
        "total_matches": total_matches,
        "shown_matches": shown_matches,
        "transactions": transactions,
        "message": (
            f"Showing {shown_matches} of {total_matches} matching transactions involving '{target}'. "
            "These are exact dataframe matches; additional matches exist when the total exceeds the number shown."
        ),
    }


# analytics
def execute_analytics(query: str, df: pd.DataFrame | None = None):

    data = _get_dataframe(df)

    if _is_exact_transaction_amount_query(query):
        exact_result = _execute_exact_transaction_query(query, data)
        if exact_result is not None:
            return exact_result

    financial_summary = summerize_financials(data)
    monthly_summary = analyze_monthly_trends(data)

    return {
        "route": QueryRoute.ANALYTICS.value,
        "query": query,
        "financial_summary": financial_summary,
        "monthly_summary": monthly_summary,
    }


# RAG
def execute_rag(query: str, k: int = 2, df: pd.DataFrame | None = None, vectorstore=None):

    # Uploaded statement RAG
    # A vague transaction-detail request should not be answered with
    # arbitrary top-k semantic matches. Ask the user to identify the
    # transaction/counterparty/reference instead.

    q = query.lower().strip()
    vague_transaction_detail_query = (
        "transaction detail" in q
        or "transaction details" in q
    ) and not any(
        phrase in q
        for phrase in (
            "involving",
            "related to",
            "with ",
            "to ",
            "from ",
            "for ",
            "reference",
            "transaction id",
        )
    )

    if vague_transaction_detail_query:
        return {
            "route": QueryRoute.RAG.value,
            "query": query,
            "results": [],
            "message": (
                "Please specify which transaction you want details for. "
                "You can provide a counterparty, transaction ID, reference "
                "number, amount, or description."
            ),
        }

    if df is not None:
        exact_search_result = _execute_exact_transaction_search(query, df)
        if exact_search_result is not None:
            return exact_search_result

    if vectorstore is not None:
        results = search_uploaded_vectorstore(vectorstore=vectorstore, query=query, k=k)

    elif df is not None:

        raise ValueError("Uploaded statement vectorstore has not been initialized.")


    # RAG fallback
    else:
        results = search_transactions(query, k=k)

    transactions = []
    for doc in results:
        transactions.append(
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
            }
        )
    return {
        "route": QueryRoute.RAG.value,
        "query": query,
        "results": transactions,
    }

# ML
def execute_ml(query: str, df: pd.DataFrame | None = None):
    data = _get_dataframe(df)
    anomaly_df = detect_anomalies(data)
    anomalies = get_anomalous_transactions(anomaly_df, n=20).copy()

    if not anomalies.empty:
        anomalies["amount_display"] = (pd.to_numeric(anomalies["amount"], errors="coerce").abs().round(2))
        anomalies["transaction_type_display"] = (
            anomalies["transaction_type"].astype(str).str.upper().map(
                {
                    "CR": "Credit",
                    "DR": "Debit",
                }
            ).fillna(anomalies["transaction_type"]))
        
    return {
        "route": QueryRoute.ML.value,
        "query": query,
        "anomalies": anomalies.to_dict(orient="records")
    }

# Hybrid
def execute_hybrid(query: str, df: pd.DataFrame | None = None):
    data = _get_dataframe(df)
    financial_summary = summerize_financials(data)
    monthly_summary = analyze_monthly_trends(data)

    month_name, month_number, requested_year = (extract_month_from_query(query))

    data["transaction_datetime"] = pd.to_datetime(data["transaction_datetime"], errors="coerce")

    target_month = None
    comparison_months = []
    if month_number is not None:
        if requested_year is None:
            matching_years = (data.loc[data["transaction_datetime"].dt.month== month_number,"transaction_datetime",].dt.year.dropna())

            if not matching_years.empty:
                requested_year = int(matching_years.max())

        if requested_year is not None:
            target_month = pd.Period(f"{requested_year}-{month_number:02d}", freq="M")
            previous_month = (target_month - 1)
            next_month = (target_month + 1)
            comparison_months = [previous_month, target_month, next_month]

    monthly_comparison = []
    if comparison_months:
        for period in comparison_months:
            month_df = data[data["transaction_datetime"].dt.to_period("M") == period].copy()
            debit_df = month_df[month_df["transaction_type"].astype(str).str.upper() == "DR"]
            credit_df = month_df[month_df["transaction_type"].astype(str).str.upper() == "CR"]

            monthly_comparison.append(
                {
                    "month": str(period),
                    "transaction_count": len(month_df),
                    "debit_count": len(debit_df),
                    "credit_count": len(credit_df),
                    "total_expense": round(debit_df["amount"].abs().sum(), 2),
                    "total_income": round(credit_df["amount"].abs().sum(), 2),
                    "average_debit": (round(debit_df["amount"].abs().mean(), 2)
                        if not debit_df.empty
                        else 0.0
                    ),
                    "average_credit": (
                        round(credit_df["amount"].abs().mean(), 2)
                        if not credit_df.empty
                        else 0.0
                    ),
                }
            )

    # Cate. comp.
    category_comparison = []
    if target_month is not None:
        for period in comparison_months:
            month_df = data[data["transaction_datetime"].dt.to_period("M") == period].copy()
            debit_df = month_df[month_df["transaction_type"].astype(str).str.upper() == "DR"]

            if debit_df.empty:
                continue

            category_column = ("transaction_category"
                if "transaction_category"
                in debit_df.columns
                else None
            )

            if category_column is None:
                continue

            category_data = (debit_df.assign(expense_amount=(debit_df["amount"].abs())).groupby(category_column, dropna=False)
                .agg(transaction_count = ("expense_amount", "count",),
                    total_expense=("expense_amount", "sum")).reset_index())

            category_data["month"] = str(period)
            category_data["total_expense"] = (category_data["total_expense"].round(2))
            category_comparison.extend(category_data.to_dict(orient="records"))


    # Major expenses
    major_transactions = []
    if target_month is not None:
        target_df = data[data["transaction_datetime"].dt.to_period("M") == target_month].copy()
        target_debits = target_df[target_df["transaction_type"].astype(str).str.upper() == "DR"].copy()
        target_debits["expense_amount"] = target_debits["amount"].abs()
        target_debits = (target_debits.sort_values("expense_amount", ascending = False).head(10))

        for _, row in target_debits.iterrows():
            major_transactions.append(
                {
                    "transaction_id": str(row.get("transaction_id", "")),
                    "date": str(row["transaction_datetime"]),
                    "amount": round(float(row["expense_amount"]), 2, ),
                    "category": str(row.get("transaction_category", "UNKNOWN")),
                    "counterparty": str(row.get("counterparty", "UNKNOWN")),
                    "payment_mode": str(row.get("payment_mode", "UNKNOWN")),
                    "description": str(row.get("description", "")),
                }
            )

    # anomaly detection
    anomaly_df = detect_anomalies(data)
    anomalies = get_anomalous_transactions(anomaly_df, n = 10)

    return {
        "route": QueryRoute.HYBRID.value,
        "query": query,
        "financial_summary": financial_summary,
        "monthly_summary": monthly_summary,
        "monthly_comparison": monthly_comparison,
        "category_comparison": category_comparison,
        "major_transactions": major_transactions,
        "anomalies": anomalies.to_dict(orient="records"),
    }


def execute_query(query: str, df: pd.DataFrame | None = None):
    route = route_query(query)
    if route == QueryRoute.ANALYTICS:
        result = execute_analytics(query, df)

    elif route == QueryRoute.RAG:
        result = execute_rag(query, df = df)

    elif route == QueryRoute.ML:
        result = execute_ml(query, df)

    elif route == QueryRoute.HYBRID:
        result = execute_hybrid(query, df)

    else:
        raise ValueError(f"Unsupported route: {route}")

    answer = generate_financial_response(query=query, context=result)
    result["answer"] = answer
    return result