from __future__ import annotations
import json

try:
    from .groq_client import generate_response
except ImportError:
    from groq_client import generate_response

SYSTEM_PROMPT = """
You are a bank statement analysis assistant.

Your job is to explain verified financial information from a bank statement.

Rules:
1. Use only the information provided in the context.
2. Do not invent transactions, amounts, dates, categories, or people.
3. Do not change or recalculate verified financial figures.
4. Python/analytics is the source of truth for numerical calculations.
5. If the context does not contain enough information to answer the question, say so.
6. Clearly distinguish facts from interpretation.
7. Use Indian Rupee formatting (₹).
8. Keep answers concise but useful.
9. Never claim that an anomaly is fraud. An anomaly only means that the ML model identified the transaction as unusual.
"""

def generate_financial_response(query: str, context: dict) -> str:
    if not query or not query.strip():
        raise ValueError("Query can't be empty.")

    if not isinstance(context, dict):
        raise ValueError("Context must be a dictionary.")

    context_text = json.dumps(context, indent=2, default=str, ensure_ascii=False)

    prompt = f"""
{SYSTEM_PROMPT}

User question:
{query}

Verified financial context:
{context_text}

Answer the user's question using the verified context above.
"""

    return generate_response(prompt)