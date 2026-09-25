import re
import pandas as pd

def clean_description(value):
    if pd.isna(value):
        return ""
    text = str(value).strip()

    text = re.sub(r"\s+", " ", text)
    return text


def extract_payment_mode(description):
    text = clean_description(description).upper()

    if text.startswith("UPI/") or "UPI/" in text:
        return "UPI"

    if text.startswith("NEFT/") or "NEFT/" in text:
        return "NEFT"

    if text.startswith("IMPS/") or "IMPS/" in text:
        return "IMPS"

    if text.startswith("RTGS/") or "RTGS/" in text:
        return "RTGS"

    if "ATM" in text:
        return "ATM"

    if "POS" in text:
        return "POS"

    if "CASH" in text:
        return "CASH"

    if "CHEQUE" in text or "CHQ" in text:
        return "CHEQUE"

    return "UNKNOWN"


def extract_upi_counterparty(description):
    text = clean_description(description)
    parts = text.split("/")

    if len(parts) < 2:
        return "UNKNOWN"

    if parts[0].strip().upper() != "UPI":
        return "UNKNOWN"

    counterparty = parts[1].strip()

    if not counterparty:
        return "UNKNOWN"

    return counterparty


def extract_upi_merchant(description):
    text = clean_description(description)

    parts = [part.strip() for part in text.split("/")]

    if len(parts) < 4:
        return "UNKNOWN"

    if parts[0].upper() != "UPI":
        return "UNKNOWN"

    message = parts[3]
    message_upper = message.upper()
    merchant_pattern = [
        "PAY TO ",
        "PAYMENT TO ",
        "SENT TO ",
        "PAID TO ",
        "TO ",
    ]

    for pattern in merchant_pattern:
        if message_upper.startswith(pattern):
            merchant = message[len(pattern):].strip()

            if merchant:
                return merchant

    return "UNKNOWN"


def extract_transaction_features(description):
    cleaned = clean_description(description)
    return {
        "description_clean": cleaned,
        "payment_mode": extract_payment_mode(cleaned),
        "counterparty": extract_upi_counterparty(cleaned),
        "merchant": extract_upi_merchant(cleaned),
    }


def add_description_features(df):

    data = df.copy()
    description_column = next(
        (
            column
            for column in ("description", "description_raw", "description_clean")
            if column in data.columns
        ),
        None,
    )
    if description_column is None:
        raise ValueError(
            "Transaction data must contain description, description_raw, "
            "or description_clean."
        )

    if "description" not in data.columns:
        data["description"] = data[description_column]

    features = data[description_column].apply(extract_transaction_features)
    feature_df = pd.DataFrame(features.tolist(), index=data.index)

    for column in feature_df.columns:
        data[column] = feature_df[column]

    return data