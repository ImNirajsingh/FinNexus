from pathlib import Path
import pandas as pd
from langchain_core.documents import Document


def load_transactions(file_path: str | Path) -> pd.DataFrame:
    """Load processed transaction data."""

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Transaction file not found: {file_path}")
    df = pd.read_csv(file_path)
    if df.empty:
        raise ValueError("Transaction dataframe is empty.")
    return df

def safe_value(value, default = "UNKNOWN"):
    """convert missnig value into a clean string."""
    if pd.isna(value):
        return default
    value = str(value).strip()
    if not value:
        return default
    return value

def create_transaction_document(row: pd.Series) -> Document:
    """Convert one transaction into a LangGraph Document."""
    transaction_id = safe_value(row.get("transaction_id"))
    date = safe_value(row.get("transaction_datetime", row.get("transaction_date")))
    transaction_type = safe_value(row.get("transaction_type"))
    amount = row.get("amount", 0)
    try :
        amount = abs(float(amount))
        amount_text = f"₹{amount:,.2f}"
    except (TypeError, ValueError):
        amount_text = "UNKNOWN"

    category = safe_value(row.get("transaction_category"))
    counterparty = safe_value(row.get("counterparty"))
    payment_mode = safe_value(row.get("payment_mode"))
    description = safe_value(row.get("description", row.get("description_clean")))
    reference_no = safe_value(row.get("reference_no"))

    # Convert CR/DR into readable format
    if transaction_type.upper() == "CR":
        transaction_direction = "Credit / Money received"
    elif transaction_type.upper() == "DR":
        transaction_direction = "Debit / Money spent"
    else:
        transaction_direction = transaction_type

    page_content = f"""

Bank Transaction 

Transaction ID: {transaction_id}
Date: {date}

Transaction Type: {transaction_direction}
Amount: {amount_text}

Category: {category}
Counterparty: {counterparty}
Payment Mode: {payment_mode}

Description: {description}
Reference Number: {reference_no}

This transaction represents a {transaction_direction.lower()}
of {amount_text} on {date}.
""".strip()


    metadata = {
        "transaction_id": transaction_id,
        "date": date,
        "transaction_type": transaction_type,
        "amount": amount,
        "category": category,
        "counterparty": counterparty,
        "payment_mode": payment_mode,
    }

    return Document(
        page_content=page_content,
        metadata= metadata
    )


def create_transaction_documents(df: pd.DataFrame) -> list[Document]:
    """Convert all transactions into LangChain Documents."""

    if df.empty:
        raise ValueError("Can't create documents from an empty dataframe.")

    documents = []
    for _, row in df.iterrows():
        document = create_transaction_document(row)
        documents.append(document)

    return documents