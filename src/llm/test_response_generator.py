from response_generator import generate_financial_response


context = {
    "route": "analytics",
    "financial_summary": {
        "total_transactions": 1793,
        "total_income": 2245208.09,
        "total_expense": 2242040.60,
        "net_cash_flow": 3167.49,
    },
    "march_2026": {
        "total_income": 189273.00,
        "total_expense": 207586.74,
        "net_cash_flow": -18313.74,
    },
}


query = "How much did I spend in March?"

answer = generate_financial_response(
    query=query,
    context=context,
)

print("=" * 80)
print("FINANCIAL AI RESPONSE")
print("=" * 80)
print(answer)