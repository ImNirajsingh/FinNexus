from typing import Any, TypedDict

class FinancialAgentState(TypedDict, total=False):
    query: str
    route: str
    context: dict[str, Any]
    answer: str
    dataframe: Any
    vectorstore: Any