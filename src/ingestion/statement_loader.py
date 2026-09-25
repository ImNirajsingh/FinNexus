from __future__ import annotations
import csv
import io
from pathlib import Path
import re
import pandas as pd

# Common names used by different banks for the same field.
COLUMN_ALIASES = {
    
    "transaction_date": ["transaction date", "transaction_date", "txn date", "txn_date", "date", "trans date", "tran date",],
    "value_date": ["value date", "value_date", "value dt",],

    "description": ["description", "description raw", "description_raw", "description clean", "description_clean", "narration",
        "transaction description", "transaction details", "particulars", "details", "remarks"],

    "reference_no": ["chq /ref no.", "chq/ref no", "cheque number", "cheque no", "reference number", "reference no",
        "ref no", "ref number", "transaction id", "transaction reference"],

    "amount": ["amount", "transaction amount", "txn amount"],

    "transaction_type": ["dr / cr", "dr/cr", "debit/credit", "debit credit", "transaction type", "transaction_type", "type", "cr/dr"],

    "debit": ["debit", "debit amount", "withdrawal", "withdrawals", "withdrawal amount"],
    "credit": ["credit", "credit amount", "deposit", "deposits", "credit amount"],
    "balance": ["balance", "closing balance", "available balance", "running balance"],
}


# Column util.

def clean_column_name(column: object) -> str:
    text = str(column).strip().lower()
    text = re.sub(r"[\r\n]+", " ", text)
    text = re.sub(r"[_/.-]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_column(df: pd.DataFrame, aliases: list[str]) -> str | None:
    normalized_columns = {
        clean_column_name(column): column
        for column in df.columns
    }
    for alias in aliases:
        normalized_alias = clean_column_name(alias)
        if normalized_alias in normalized_columns:
            return normalized_columns[normalized_alias]

    return None


# Num. cleaning
def clean_numeric_series(series: pd.Series) -> pd.Series:
    cleaned = (series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("₹", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.replace("€", "", regex=False)
        .str.strip()
    )
    return pd.to_numeric(cleaned, errors="coerce")


# Trans. type normalization
def normalize_transaction_type(value: object) -> str:
    if pd.isna(value):
        return "UNKNOWN"

    text = str(value).strip().upper()
    if text in {"CR", "CREDIT", "C", "CR."}:
        return "CR"

    if text in {"DR", "DEBIT", "D", "DR."}:
        return "DR"

    return "UNKNOWN"


def _read_malformed_csv(file) -> pd.DataFrame:

    if hasattr(file, "getvalue"):
        raw_bytes = file.getvalue()
        if not raw_bytes:
            raise ValueError("The CSV file is empty.")

        raw_text = raw_bytes.decode("utf-8-sig", errors="replace")

    elif hasattr(file, "read"):
        file.seek(0)
        raw_data = file.read()
        if not raw_data:
            raise ValueError("The CSV file is empty.")

        if isinstance(raw_data, bytes):
            raw_text = raw_data.decode("utf-8-sig", errors="replace")

        else:
            raw_text = raw_data

    else:
        raw_text = Path(file).read_text(encoding="utf-8", errors="replace")

    if not raw_text.strip():
        raise ValueError("The CSV file is empty.")

    rows = []
    for line in raw_text.splitlines():
        if not line.strip():
            continue

        if line.strip().startswith("#"):
            continue

        try:
            rows.append(next(csv.reader([line])))

        except csv.Error:
            continue

    if not rows:
        raise ValueError("No valid rows were found in the uploaded CSV file.")

    base_header = [
        "transaction_id",
        "transaction_date",
        "value_date",
        "description_raw",
        "description_clean",
        "reference_no",
        "amount",
        "transaction_type",
        "balance",
        "balance_type1",
    ]

    for index, row in enumerate(rows):
        if len(row) <= len(base_header):
            continue

        normalized_header = [
            clean_column_name(cell)
            for cell in row[:len(base_header)]
        ]

        expected_header = [
            clean_column_name(cell)
            for cell in base_header
        ]

        if normalized_header == expected_header:
            repaired = io.StringIO()
            writer = csv.writer(repaired)
            writer.writerow(row[:len(base_header)])
            writer.writerow(row[len(base_header):])

            for extra_row in rows[index + 1:]:
                writer.writerow(extra_row)

            repaired.seek(0)
            return pd.read_csv(repaired, comment="#")

    for row in rows:
        if len(row) > len(base_header):
            repaired = io.StringIO()
            writer = csv.writer(repaired)
            writer.writerow(base_header)
            writer.writerow(row[len(base_header):])

            for extra_row in rows[1:]:
                if extra_row is not row:
                    writer.writerow(extra_row)

            repaired.seek(0)
            return pd.read_csv(repaired, comment="#")

    raise ValueError("Could not parse the uploaded CSV into a valid bank statement structure.")


def _resolve_statement_path(file) -> str | Path:
    
    if hasattr(file, "name"):
        return file

    candidate = Path(file)
    if candidate.exists():
        return candidate

    project_root = Path(__file__).resolve().parents[2]
    fallback_candidates = [
        project_root / "data" / candidate.name,
        project_root / "data" / "raw" / candidate.name,
        project_root / "data" / "AccountStatement_18-Sep-2025_18-Sep-2026.csv",
        project_root / "data" / "raw" / "bank_statement.csv",
    ]

    for fallback in fallback_candidates:
        if fallback.exists():
            return fallback

    return candidate


def load_statement(file) -> pd.DataFrame:
    
    resolved_file = _resolve_statement_path(file)
    filename = getattr(resolved_file, "name", str(resolved_file))
    extension = Path(filename).suffix.lower()

    if extension == ".csv":
        try:
            if hasattr(file, "getvalue"):
                raw_bytes = file.getvalue()
                if not raw_bytes:
                    raise ValueError("The CSV file is empty.")

                frame = pd.read_csv(io.BytesIO(raw_bytes), comment="#")

            elif hasattr(file, "read"):
                file.seek(0)
                frame = pd.read_csv(resolved_file, comment="#")

            else:
                frame = pd.read_csv(resolved_file, comment="#")

            normalized_columns = [
                clean_column_name(column)
                for column in frame.columns
            ]

            if (
                not frame.empty
                and len(frame.columns) > 0
                and "transaction date" in normalized_columns
                and len(frame.columns) <= 10
            ):
                return frame
            return _read_malformed_csv(resolved_file)
        
        except pd.errors.EmptyDataError as exc:
            raise ValueError("The CSV file is empty or contains only placeholder text. Please upload a valid bank statement CSV.") from exc

        except ValueError:
            raise
        except Exception:
            return _read_malformed_csv(resolved_file)

    if extension in {".xlsx", ".xls"}:
        if hasattr(file, "seek"):
            file.seek(0)

        return pd.read_excel(file)

    raise ValueError("Unsupported file type. Please upload CSV, XLSX, or XLS.")


def normalize_statement(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:

    if df.empty:
        raise ValueError("The uploaded statement is empty.")
    
    data = df.copy()
    warnings: list[str] = []

    date_column = find_column(data, COLUMN_ALIASES["transaction_date"])
    description_column = find_column(data, COLUMN_ALIASES["description"])
    amount_column = find_column(data,COLUMN_ALIASES["amount"],)
    type_column = find_column(data, COLUMN_ALIASES["transaction_type"])
    debit_column = find_column(data, COLUMN_ALIASES["debit"])
    credit_column = find_column(data, COLUMN_ALIASES["credit"])
    balance_column = find_column(data, COLUMN_ALIASES["balance"])
    reference_column = find_column(data, COLUMN_ALIASES["reference_no"])
    value_date_column = find_column(data, COLUMN_ALIASES["value_date"])

    if date_column is None:
        raise ValueError("Could not identify the transaction date column.")

    data["transaction_datetime"] = pd.to_datetime(data[date_column], errors="coerce", dayfirst=True)
    invalid_dates = (data["transaction_datetime"].isna().sum())

    if invalid_dates:
        warnings.append(f"{invalid_dates} rows have invalid transaction dates.")
    if description_column is not None:
        data["description"] = (data[description_column].fillna("").astype(str).str.strip())

    else:
        data["description"] = ""
        warnings.append("No description/narration column was detected.")

    if reference_column is not None:
        data["reference_no"] = (data[reference_column].fillna("").astype(str).str.strip())

    else:
        data["reference_no"] = ""

    if value_date_column is not None:
        data["value_date"] = pd.to_datetime(data[value_date_column], errors="coerce", dayfirst=True,)

    else:
        data["value_date"] = (data["transaction_datetime"])

    if amount_column is not None:
        data["amount"] = clean_numeric_series(data[amount_column])

        if type_column is not None:
            data["transaction_type"] = (data[type_column].apply(normalize_transaction_type))

        elif (
            debit_column is not None 
            or credit_column is not None
        ):

            debit_values = (clean_numeric_series(data[debit_column])
                if debit_column is not None
                else pd.Series(0, index=data.index)
            )

            credit_values = (clean_numeric_series(data[credit_column])
                if credit_column is not None
                else pd.Series(0, index=data.index)
            )

            data["transaction_type"] = "UNKNOWN"
            data.loc[credit_values.notna() & (credit_values != 0), "transaction_type"] = "CR"
            data.loc[debit_values.notna() & (debit_values != 0), "transaction_type"] = "DR"
            data["amount"] = (data["amount"].fillna(debit_values).fillna(credit_values))

        else:
            warnings.append("Amount was detected, but debit/credit direction could not be identified.")
            data["transaction_type"] = "UNKNOWN"

    elif (
        debit_column is not None
        or credit_column is not None
    ):
        debit_values = (clean_numeric_series(data[debit_column])
            if debit_column is not None
            else pd.Series(0, index=data.index)
        )

        credit_values = (clean_numeric_series(data[credit_column])
            if credit_column is not None
            else pd.Series(0, index=data.index)
        )

        data["amount"] = (debit_values.fillna(credit_values))
        data["transaction_type"] = "UNKNOWN"
        data.loc[credit_values.notna() & (credit_values != 0), "transaction_type"] = "CR"
        data.loc[debit_values.notna() & (debit_values != 0), "transaction_type"] = "DR"

    else:
        raise ValueError("Could not identify an amount column or separate debit/credit columns.")

    if balance_column is not None:
        data["balance"] = clean_numeric_series(data[balance_column])

    else:
        data["balance"] = pd.NA
        warnings.append("No balance column was detected.")

    data["transaction_id"] = [
        f"TXN{i:06d}"
        for i in range(1, len(data) + 1)
    ]

    standard_columns = [
        "transaction_id",
        "transaction_datetime",
        "value_date",
        "description",
        "reference_no",
        "amount",
        "transaction_type",
        "balance",
    ]

    normalized = data[standard_columns].copy()
    normalized = normalized[normalized["transaction_datetime"].notna() & normalized["amount"].notna()].copy()
    normalized.reset_index(drop=True, inplace=True)

    return normalized, warnings