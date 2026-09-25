from groq_client import generate_response


prompt = """
You are a bank statement analysis assistant.

Answer the following question using only the provided information.

Question:
How much did I spend in March 2026?

Verified financial data:
March 2026 total expense = ₹207,586.74

Do not perform any additional calculations.
Do not invent information.
"""

answer = generate_response(prompt)

print("=" * 80)
print("GROQ RESPONSE")
print("=" * 80)
print(answer)