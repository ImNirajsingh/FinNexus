from __future__ import annotations

from functools import lru_cache

import pandas as pd

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


# ---------------------------------------------------------
# Embeddings
# ---------------------------------------------------------

@lru_cache(maxsize=1)
def get_embeddings():

    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


# ---------------------------------------------------------
# DataFrame → LangChain Documents
# ---------------------------------------------------------

def dataframe_to_documents(
    df: pd.DataFrame,
) -> list[Document]:

    if df.empty:
        return []

    documents = []

    for _, row in df.iterrows():

        transaction_type = str(
            row.get(
                "transaction_type",
                "UNKNOWN",
            )
        ).upper()

        if transaction_type == "DR":
            transaction_type_text = "Debit / Money spent"

        elif transaction_type == "CR":
            transaction_type_text = "Credit / Money received"

        else:
            transaction_type_text = transaction_type

        amount = row.get(
            "amount_abs",
            row.get("amount", 0),
        )

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            amount = 0.0

        transaction_id = str(
            row.get(
                "transaction_id",
                "",
            )
        )

        transaction_date = str(
            row.get(
                "transaction_datetime",
                row.get("date", ""),
            )
        )

        description = str(
            row.get(
                "description",
                "",
            )
        )

        counterparty = str(
            row.get(
                "counterparty",
                "UNKNOWN",
            )
        )

        payment_mode = str(
            row.get(
                "payment_mode",
                "UNKNOWN",
            )
        )

        category = str(
            row.get(
                "transaction_category",
                "UNKNOWN",
            )
        )

        reference_no = str(
            row.get(
                "reference_no",
                "",
            )
        )

        page_content = f"""
Bank Transaction

Transaction ID: {transaction_id}
Date: {transaction_date}
Transaction Type: {transaction_type_text}
Amount: ₹{amount:,.2f}
Category: {category}
Counterparty: {counterparty}
Payment Mode: {payment_mode}
Description: {description}
Reference Number: {reference_no}

This transaction represents
{transaction_type_text.lower()}
of ₹{amount:,.2f}.
""".strip()

        metadata = {
            "transaction_id": transaction_id,
            "date": transaction_date,
            "transaction_type": transaction_type,
            "amount": amount,
            "category": category,
            "counterparty": counterparty,
            "payment_mode": payment_mode,
        }

        documents.append(
            Document(
                page_content=page_content,
                metadata=metadata,
            )
        )

    return documents


# ---------------------------------------------------------
# Create vectorstore
# ---------------------------------------------------------

def create_uploaded_vectorstore(
    df: pd.DataFrame,
) -> Chroma:

    documents = dataframe_to_documents(df)

    if not documents:
        raise ValueError(
            "Cannot create a vectorstore from an empty statement."
        )

    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=get_embeddings(),
        collection_name="uploaded_bank_statement",
    )

    return vectorstore


# ---------------------------------------------------------
# Search existing vectorstore
# ---------------------------------------------------------

def search_uploaded_vectorstore(
    vectorstore: Chroma,
    query: str,
    k: int = 2,
):

    return vectorstore.similarity_search(
        query,
        k=k,
    )


# ---------------------------------------------------------
# Backward-compatible API used by the graph route executor
# ---------------------------------------------------------

def search_uploaded_transactions(
    df: pd.DataFrame | None = None,
    query: str = "",
    k: int = 2,
    vectorstore: Chroma | None = None,
):
    """Search uploaded transactions using either an existing vectorstore or a dataframe."""

    if vectorstore is not None:
        return search_uploaded_vectorstore(
            vectorstore=vectorstore,
            query=query,
            k=k,
        )

    if df is None or df.empty:
        return []

    vectorstore = create_uploaded_vectorstore(df)

    return search_uploaded_vectorstore(
        vectorstore=vectorstore,
        query=query,
        k=k,
    )