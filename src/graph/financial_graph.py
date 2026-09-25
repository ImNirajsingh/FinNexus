from __future__ import annotations
from pathlib import Path
import sys
from langgraph.graph import END, START, StateGraph

SRC_DIR = Path(__file__).resolve().parents[1]

if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

try:
    from src.graph.query_router import QueryRoute, route_query
    from src.graph.route_executor import execute_analytics, execute_rag, execute_ml, execute_hybrid
    from src.graph.state import FinancialAgentState
except ImportError:  # pragma: no cover
    from query_router import QueryRoute, route_query
    from route_executor import execute_analytics, execute_rag, execute_ml, execute_hybrid
    from state import FinancialAgentState
from llm.response_generator import generate_financial_response

# Router
def router_node(state: FinancialAgentState):
    query = state["query"]
    route = route_query(query)
    return {
        "route": route.value
    }

# analytics
def analytics_node(state: FinancialAgentState):
    query = state["query"]
    df = state["dataframe"]
    result = execute_analytics(query, df)
    return {
        "context": result
    }

# RAG
def rag_node(state: FinancialAgentState):
    query = state["query"]
    vectorstore = state["vectorstore"]
    result = execute_rag(query, k=2, vectorstore=vectorstore)
    return {
        "context": result
    }

# ml
def ml_node(state: FinancialAgentState):
    query = state["query"]
    df = state["dataframe"]
    result = execute_ml(query, df)
    return {
        "context": result
    }

# Hybrid
def hybrid_node(state: FinancialAgentState):
    query = state["query"]
    df = state["dataframe"]
    result = execute_hybrid(query, df)
    return {
        "context": result
    }

# generate answer
def answer_node(state: FinancialAgentState):
    query = state["query"]
    context = state["context"]
    answer = generate_financial_response(query=query,context=context)
    return {
        "answer": answer
    }


# =========================================================
# Routing
# =========================================================

def route_from_state(state: FinancialAgentState):
    route = state["route"]
    if route == QueryRoute.ANALYTICS.value:
        return "analytics"
    
    if route == QueryRoute.RAG.value:
        return "rag"

    if route == QueryRoute.ML.value:
        return "ml"

    if route == QueryRoute.HYBRID.value:
        return "hybrid"

    raise ValueError(f"Unsupported route: {route}")

# build graph
def build_financial_graph():
    graph = StateGraph(FinancialAgentState)

    # Nodes
    graph.add_node("router", router_node)
    graph.add_node("analytics", analytics_node)
    graph.add_node("rag", rag_node)
    graph.add_node("ml", ml_node)
    graph.add_node("hybrid", hybrid_node)
    graph.add_node("answer", answer_node)

    # START -> router
    graph.add_edge(START, "router")

    # router -> route
    graph.add_conditional_edges("router",route_from_state,
        {
            "analytics": "analytics",
            "rag": "rag",
            "ml": "ml",
            "hybrid": "hybrid"
        },
    )
    # route -> answer
    graph.add_edge("analytics", "answer")
    graph.add_edge("rag", "answer")
    graph.add_edge("ml", "answer")
    graph.add_edge("hybrid", "answer")

    # answer → END
    graph.add_edge("answer", END)

    return graph.compile()


# compile
financial_graph = build_financial_graph()