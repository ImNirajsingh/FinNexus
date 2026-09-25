from enum import Enum
class QueryRoute(str, Enum):
    ANALYTICS = "analytics"
    RAG = "rag"
    ML = "ml"
    HYBRID = "hybrid"


def route_query(query: str) -> QueryRoute:
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")
    q = query.lower().strip()
    ml_keywords = [
        "anomal",
        "unusual transaction",
        "unusual payment",
        "suspicious transaction",
        "outlier",
        "abnormal transaction",
        "unexpected transaction",
    ]

    if any(keyword in q for keyword in ml_keywords):
        return QueryRoute.ML

    hybrid_keywords = [
    "why did my spending",
    "why was my spending",
    "why did expenses",
    "why did my expenses",
    "why was my expense",
    "why were my expenses",
    "spending increase",
    "spending decrease",
    "expense increase",
    "expense decrease",
    "expenses increase",
    "expenses decrease",
    "compare my spending",
    "what caused my spending",
    "what caused my expenses",
    "major recurring expenses",
]

    if any(keyword in q for keyword in hybrid_keywords):
        return QueryRoute.HYBRID
    
    analytical_keywords = [
        "how much",
        "total",
        "sum",
        "average",
        "median",
        "largest",
        "highest",
        "lowest",
        "smallest",
        "income",
        "expense",
        "expenses",
        "spent",
        "spending",
        "cash flow",
        "balance",
        "monthly",
        "month",
        "category",
        "categories",
        "how many transactions",
        "number of transactions",
    ]

    if any(keyword in q for keyword in analytical_keywords):
        return QueryRoute.ANALYTICS

    rag_keywords = [
        "show transactions",
        "find transactions",
        "transaction involving",
        "transactions involving",
        "payment involving",
        "payments involving",
        "related to",
        "paid to",
        "payment to",
        "sent to",
        "received from",
        "transaction with",
        "transactions with",
        "merchant",
        "counterparty",
        "upi transaction",
    ]

    if any(keyword in q for keyword in rag_keywords):
        return QueryRoute.RAG

    # Default
    return QueryRoute.RAG