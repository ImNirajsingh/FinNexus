from pathlib import Path
import sys

import pandas as pd


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


# ---------------------------------------------------------
# Imports
# ---------------------------------------------------------

from ingestion.statement_loader import normalize_statement

from preprocessing.uploaded_statement_features import (
    add_uploaded_statement_features,
)

from rag.uploaded_retriever import (
    create_uploaded_vectorstore,
)

from financial_graph import financial_graph


# ---------------------------------------------------------
# Real processed statement
# ---------------------------------------------------------

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "transactions_features_v2.csv"
)


# ---------------------------------------------------------
# Load statement
# ---------------------------------------------------------

raw_df = pd.read_csv(
    DATA_FILE
)

print("=" * 70)
print("RAW STATEMENT")
print("=" * 70)

print(
    f"Transactions: {len(raw_df):,}"
)

print(
    f"Columns: {len(raw_df.columns)}"
)


# ---------------------------------------------------------
# Normalize
# ---------------------------------------------------------

normalized_df, warnings = normalize_statement(
    raw_df
)

print()
print("=" * 70)
print("NORMALIZED STATEMENT")
print("=" * 70)

print(
    f"Transactions: {len(normalized_df):,}"
)


# ---------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------

statement_df = (
    add_uploaded_statement_features(
        normalized_df
    )
)

print()
print("=" * 70)
print("FEATURE ENGINEERED STATEMENT")
print("=" * 70)

print(
    f"Transactions: {len(statement_df):,}"
)


# ---------------------------------------------------------
# Create uploaded RAG vectorstore ONCE
# ---------------------------------------------------------

print()
print("=" * 70)
print("CREATING RAG VECTORSTORE")
print("=" * 70)

uploaded_vectorstore = (
    create_uploaded_vectorstore(
        statement_df
    )
)

print(
    "Uploaded statement vectorstore created successfully."
)


# ---------------------------------------------------------
# Analytics
# ---------------------------------------------------------

analytics_query = (
    "How much did I spend in March 2026?"
)

analytics_result = financial_graph.invoke(
    {
        "query": analytics_query,
        "dataframe": statement_df,
    }
)

print()
print("=" * 70)
print("ANALYTICS TEST")
print("=" * 70)

print(
    f"Question:\n{analytics_query}"
)

print(
    f"\nRoute:\n{analytics_result['route']}"
)

print(
    f"\nAnswer:\n{analytics_result['answer']}"
)


# ---------------------------------------------------------
# RAG
# ---------------------------------------------------------

rag_query = (
    "Show transactions involving Akhilesh Yadav"
)

rag_result = financial_graph.invoke(
    {
        "query": rag_query,
        "dataframe": statement_df,
        "vectorstore": uploaded_vectorstore,
    }
)

print()
print("=" * 70)
print("RAG TEST")
print("=" * 70)

print(
    f"Question:\n{rag_query}"
)

print(
    f"\nRoute:\n{rag_result['route']}"
)

print(
    f"\nAnswer:\n{rag_result['answer']}"
)


# ---------------------------------------------------------
# ML
# ---------------------------------------------------------

ml_query = (
    "What unusual transactions occurred?"
)

ml_result = financial_graph.invoke(
    {
        "query": ml_query,
        "dataframe": statement_df,
    }
)

print()
print("=" * 70)
print("ML TEST")
print("=" * 70)

print(
    f"Question:\n{ml_query}"
)

print(
    f"\nRoute:\n{ml_result['route']}"
)

print(
    f"\nAnswer:\n{ml_result['answer']}"
)


# ---------------------------------------------------------
# Hybrid
# ---------------------------------------------------------

hybrid_query = (
    "Why was my spending higher in March 2026 "
    "than February 2026?"
)

hybrid_result = financial_graph.invoke(
    {
        "query": hybrid_query,
        "dataframe": statement_df,
    }
)

print()
print("=" * 70)
print("HYBRID TEST")
print("=" * 70)

print(
    f"Question:\n{hybrid_query}"
)

print(
    f"\nRoute:\n{hybrid_result['route']}"
)

print(
    f"\nAnswer:\n{hybrid_result['answer']}"
)