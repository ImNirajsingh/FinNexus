from pathlib import Path
import sys
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

for entry in (str(PROJECT_ROOT), str(SRC_DIR)):
    if entry not in sys.path:
        sys.path.insert(0, entry)


from src.ingestion.statement_loader import load_statement, normalize_statement
from src.preprocessing.uploaded_statement_features import add_uploaded_statement_features
from src.analytics.financial_metrics import summerize_financials, get_highest_expenses, get_highest_income
from src.analytics.monthly_analysis import analyze_monthly_trends
from src.rag.uploaded_retriever import create_uploaded_vectorstore
from src.graph.financial_graph import financial_graph


st.set_page_config(page_title="FinNexus - Financial Retrieval & Analytics System", layout="wide")


if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []

if "statement_key" not in st.session_state:
    st.session_state["statement_key"] = None

if "vectorstore" not in st.session_state:
    st.session_state["vectorstore"] = None


st.markdown(
    """
    <style>
        .main {
            background-color: #ffffff;
        }

        .block-container {
            max-width: 1200px;
            padding-top: 2rem;
        }

        h1 {
            color: #8B0000;
        }

        .subtitle {
            color: #666666;
            font-size: 1.05rem;
            margin-bottom: 2rem;
        }

        .upload-box {
            border: 1px solid #eeeeee;
            border-radius: 12px;
            padding: 1.5rem;
            background-color: #fafafa;
        }

        .success-box {
            padding: 1rem;
            border-radius: 10px;
            background-color: #f5fff7;
            border: 1px solid #ccebd3;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# header
st.title("FinNexus - Financial Retrieval & Analytics System")
st.markdown(
    '<div class="subtitle">'
    "Upload your bank statement and ask questions about your finances."
    "</div>",
    unsafe_allow_html=True,
)

# upload
st.subheader("Upload Bank Statement")
uploaded_file = st.file_uploader(
    "Upload CSV or Excel statement",
    type=["csv", "xlsx", "xls"],
    help="PDF support will be added in the next ingestion step.",
)

if uploaded_file is not None:
    try:
        statement_key = (uploaded_file.name, uploaded_file.size)
        is_new_statement = (st.session_state.get("statement_key") != statement_key)

        if is_new_statement:
            raw_df = load_statement(uploaded_file)
            normalized_df, warnings = normalize_statement(raw_df)
            features_df = add_uploaded_statement_features(normalized_df)
            st.session_state["statement_df"] = (features_df)
            st.session_state["statement_filename"] = (uploaded_file.name)
            st.session_state["raw_statement_df"] = (raw_df)
            st.session_state["normalized_statement_df"] = (normalized_df)

            with st.spinner("Preparing AI search..."):
                st.session_state["vectorstore"] = (create_uploaded_vectorstore(features_df))

            st.session_state["chat_messages"] = []
            st.session_state["statement_key"] = (statement_key)

        else:
            normalized_df = (st.session_state["normalized_statement_df"])
            features_df = (st.session_state["statement_df"])
            warnings = []

        st.success(
            f"Statement analyzed successfully: "
            f"{len(features_df):,} transactions detected."
        )

        st.subheader("Statement Overview")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Transactions", f"{len(normalized_df):,}")

        with col2:
            st.metric("Credits", f"{(normalized_df["transaction_type"] == "CR").sum():,}")

        with col3:
            st.metric("Debits", f"{(normalized_df["transaction_type"] == "DR").sum():,}")

        if warnings:
            st.warning("Some fields could not be identified automatically.")
            for warning in warnings:
                st.write(f"• {warning}")

        st.subheader("Transaction Preview")
        preview_df = features_df.copy()
        if "transaction_datetime" in preview_df.columns:
            preview_df["transaction_datetime"] = (preview_df["transaction_datetime"].dt.strftime("%Y-%m-%d"))

        if "value_date" in preview_df.columns:
            preview_df["value_date"] = (preview_df["value_date"].dt.strftime("%Y-%m-%d"))

        st.dataframe(preview_df.head(20), use_container_width=True, hide_index=True)

    except Exception as exc:
        st.error(f"Could not process the uploaded statement: {exc}")

else:
    st.info("Upload a bank statement to begin.")

if "statement_df" in st.session_state:
    df = st.session_state["statement_df"]
    st.divider()
    st.header("Financial Overview")
    summary = summerize_financials(df)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Income", f"₹{summary['total_income']:,.2f}")

    with col2:
        st.metric("Total Expense", f"₹{summary['total_expense']:,.2f}")

    with col3:
        st.metric("Net Cash Flow", f"₹{summary['net_cash_flow']:,.2f}")

    with col4:
        st.metric("Transactions", f"{summary['total_transactions']:,}")

    st.subheader("Monthly Income vs Expense")
    monthly_df = analyze_monthly_trends(df)

    if not monthly_df.empty:
        chart_df = monthly_df.set_index("month")[
            [
                "total_income",
                "total_expense",
            ]
        ]
        st.line_chart(chart_df)
    else:
        st.info("No monthly transaction data available.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Largest Expenses")
        expenses = get_highest_expenses(df, n=10)

        if not expenses.empty:
            expense_columns = [column
                for column in ["transaction_datetime", "description", "amount_abs", "transaction_type"]
                if column in expenses.columns
            ]
            display_expenses = expenses[expense_columns].copy()
            if "amount_abs" in display_expenses.columns:
                display_expenses["amount_abs"] = (display_expenses["amount_abs"].round(2))

            st.dataframe(display_expenses, use_container_width=True, hide_index=True)

        else:
            st.info("No expense transactions found.")

    with col2:
        st.subheader("Largest Income")
        income = get_highest_income(df, n=10)
        if not income.empty:
            income_columns = [column
                for column in ["transaction_datetime", "description", "amount_abs", "transaction_type"]
                if column in income.columns
            ]

            display_income = income[income_columns].copy()
            if "amount_abs" in display_income.columns:
                display_income["amount_abs"] = (display_income["amount_abs"].round(2))

            st.dataframe(display_income, use_container_width=True, hide_index=True)

        else:
            st.info("No income transactions found.")


if "statement_df" in st.session_state:
    st.divider()
    st.header("AI Financial Assistant")
    st.caption("Ask questions about your uploaded bank statement.")

    for message in st.session_state["chat_messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_question = st.chat_input("Ask about your transactions, spending, income, anomalies...")

    if user_question:
        st.session_state["chat_messages"].append(
            {
                "role": "user",
                "content": user_question,
            }
        )
        with st.chat_message("user"):
            st.markdown(user_question)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing your statement..."):

                try:
                    result = financial_graph.invoke(
                        {
                            "query": user_question,
                            "dataframe": (st.session_state["statement_df"]),
                            "vectorstore": (st.session_state["vectorstore"])})

                    answer = result.get("answer", "I could not generate an answer.")
                    route = result.get("route", "unknown")
                    st.markdown(answer)

                    with st.expander("View analysis route"):
                        st.write(f"Route: `{route}`")

                except Exception as exc:
                    answer = ("I encountered an error while analyzing the statement.")
                    st.error(f"{answer}\n\n{exc}")

        st.session_state["chat_messages"].append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

if "statement_df" in st.session_state:
    st.divider()
    st.header("Transactions Explorer")
    transactions_df = (st.session_state["statement_df"].copy())

    search_query = st.text_input("Search transactions",
        placeholder=(
            "Search description, counterparty, "
            "merchant, reference number..."
        ),
    )

    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        transaction_type_filter = st.selectbox("Transaction Type",options=["All", "Credit", "Debit"])

    with filter_col2:
        if "payment_mode" in transactions_df.columns:
            payment_modes = (transactions_df["payment_mode"].fillna("UNKNOWN").astype(str).str.strip().replace
                (
                    "",
                    "UNKNOWN",
                ).unique().tolist())

            payment_modes = sorted(payment_modes)

        else:
            payment_modes = []

        selected_payment_mode = st.selectbox("Payment Mode",options=["All"] + payment_modes)

    with filter_col3:
        if "counterparty" in transactions_df.columns:
            counterparties = (transactions_df["counterparty"].fillna("UNKNOWN").astype(str).str.strip().replace
                (
                    "",
                    "UNKNOWN",
                ).unique().tolist())

            counterparties = sorted(counterparties)

        else:
            counterparties = []
        selected_counterparty = st.selectbox("Counterparty",options=["All"] + counterparties)

    if "transaction_datetime" in transactions_df.columns:
        valid_dates = transactions_df["transaction_datetime"].dropna()

        if not valid_dates.empty:
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()
            date_range = st.date_input("Date Range",value=(min_date, max_date,), min_value=min_date, max_value=max_date)

        else:
            date_range = None

    else:
        date_range = None

    if "amount_abs" in transactions_df.columns:
        amount_values = pd.to_numeric(transactions_df["amount_abs"], errors="coerce").dropna()

    else:
        amount_values = pd.to_numeric(transactions_df["amount"], errors="coerce").abs().dropna()

    if not amount_values.empty:
        min_amount = float(amount_values.min())
        max_amount = float(amount_values.max())
        amount_range = st.slider("Amount Range", min_value=min_amount, max_value=max_amount,
            value=(
                min_amount,
                max_amount,
            ), step=1.0)

    else:
        amount_range = None

    filtered_df = (transactions_df.copy())
    if search_query.strip():
        search_text = (search_query.strip().lower())
        searchable_columns = [column
            for column in [
                "description",
                "description_clean",
                "counterparty",
                "merchant",
                "reference_no",
                "payment_mode",
            ]
            if column in filtered_df.columns
        ]
        if searchable_columns:
            search_mask = (filtered_df[searchable_columns].fillna("").astype(str).apply(lambda row:row.str.lower().str.contains
                    (
                        search_text,
                        regex=False,
                    ).any(),axis=1))

            filtered_df = (filtered_df[search_mask])

    if transaction_type_filter == "Credit":
        filtered_df = (filtered_df[filtered_df["transaction_type"] == "CR"])

    elif transaction_type_filter == "Debit":
        filtered_df = (filtered_df[filtered_df["transaction_type"] == "DR"])

    if (selected_payment_mode != "All" and "payment_mode" in filtered_df.columns):
        filtered_df = (filtered_df[filtered_df["payment_mode"].fillna("UNKNOWN").astype(str).eq(selected_payment_mode)])

    if (selected_counterparty != "All" and "counterparty" in filtered_df.columns):
        filtered_df = (filtered_df[filtered_df["counterparty"].fillna("UNKNOWN").astype(str).eq(selected_counterparty)])

    if (date_range is not None and len(date_range) == 2 and "transaction_datetime"in filtered_df.columns):
        start_date = pd.Timestamp(date_range[0])
        end_date = (pd.Timestamp(date_range[1])+ pd.Timedelta(days=1))
        filtered_df = (filtered_df[(filtered_df["transaction_datetime"] >= start_date) &(filtered_df["transaction_datetime"] < end_date )])

    if amount_range is not None:
        amount_column = ("amount_abs"
            if "amount_abs" in filtered_df.columns
            else "amount"
        )
        filtered_amount = pd.to_numeric(filtered_df[amount_column], errors="coerce").abs()
        filtered_df = (filtered_df[filtered_amount.between(amount_range[0], amount_range[1])])

    st.subheader("Filtered Transactions")
    summary_col1, summary_col2, summary_col3 = st.columns(3)

    with summary_col1:
        st.metric("Matching Transactions", f"{len(filtered_df):,}",)

    with summary_col2:
        debit_total = filtered_df.loc[filtered_df["transaction_type"] == "DR", "amount_abs",].sum()
        st.metric("Matching Expenses", f"₹{debit_total:,.2f}",)

    with summary_col3:
        credit_total = filtered_df.loc[filtered_df["transaction_type"] == "CR", "amount_abs"].sum()
        st.metric("Matching Income", f"₹{credit_total:,.2f}")

    display_columns = [
        column
        for column in [
            "transaction_id",
            "transaction_datetime",
            "description",
            "counterparty",
            "merchant",
            "payment_mode",
            "amount_abs",
            "transaction_type",
            "balance",
            "reference_no",
        ]
        if column in filtered_df.columns
    ]

    display_df = (filtered_df[display_columns].copy())
    display_df = display_df.rename(
        columns={
            "transaction_id": "Transaction ID",
            "transaction_datetime": "Date",
            "description": "Description",
            "counterparty": "Counterparty",
            "merchant": "Merchant",
            "payment_mode": "Payment Mode",
            "amount_abs": "Amount",
            "transaction_type": "Type",
            "balance": "Balance",
            "reference_no": "Reference",
        }
    )

    if "Type" in display_df.columns:
        display_df["Type"] = (display_df["Type"].map(
                {
                    "CR": "Credit",
                    "DR": "Debit",
                }
            ).fillna(display_df["Type"]))

    for column in ["Amount","Balance",]:
        if column in display_df.columns:
            display_df[column] = (pd.to_numeric(display_df[column], errors="coerce").round(2))

    st.dataframe(display_df, use_container_width=True, hide_index=True)