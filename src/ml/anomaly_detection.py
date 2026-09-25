import pandas as pd
from sklearn.ensemble import IsolationForest


def detect_anomalies(df: pd.DataFrame, contamination: float = 0.42, random_state: int = 42) -> pd.DataFrame:
    data = df.copy()
    required_columns = ["amount", "transaction_type", "days_since_previous_transaction"]
    date_column = next(
        (column for column in ("transaction_datetime", "transaction_date") if column in data.columns),
        None,
    )
    if "days_since_previous_transaction" not in data.columns and date_column:
        dates = pd.to_datetime(data[date_column], errors="coerce")
        data["days_since_previous_transaction"] = dates.sort_values().diff().dt.total_seconds().div(86400)

    missing_columns = [column for column in required_columns if column not in data.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    if data.empty:
        raise ValueError("Cannot detect anomalies in an empty transaction dataset.")

    data["amount_abs"] = pd.to_numeric(data["amount"], errors='coerce').abs()
    data["days_since_previous_transaction"] = pd.to_numeric(
        data["days_since_previous_transaction"], errors='coerce'
    )
    if "hour" in data.columns:
        data["hour"] = pd.to_numeric(data["hour"], errors='coerce')

    feature_column = ["amount_abs", "days_since_previous_transaction"]
    if "hour" in data.columns:
        feature_column.append("hour")
    model_data = data[feature_column].copy()
    model_data = model_data.fillna(model_data.median(numeric_only=True))
    model_data = model_data.fillna(0)
    model = IsolationForest(n_estimators=200, contamination = contamination, random_state = random_state, n_jobs=-1)

    predictions = model.fit_predict(model_data)
    scores = model.decision_function(model_data)

    data["is_anomaly"] = predictions == -1
    data["anomaly_score"] = scores
    data["anomaly_rank"] = data["anomaly_score"].rank(method="first", ascending=True).astype(int)
    data = data.drop(columns=["amount_abs"], errors='ignore')
    return data


def get_anomalous_transactions(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    if "is_anomaly" not in df.columns:
        raise ValueError("Run detect_anomalies() before calling "
                         "get_anomalies_transactions().")
    return( df[df["is_anomaly"]].sort_values("anomaly_score", ascending=True).head(n))