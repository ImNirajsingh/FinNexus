from route_executor import execute_query


queries = [
    "How much did I spend in March?",
    "Show transactions involving Akhilesh Yadav",
    "What unusual transactions occurred?",
    "Why was my spending higher in March?",
]


for query in queries:
    print("=" * 80)
    print(f"QUESTION: {query}")
    print("=" * 80)

    result = execute_query(query)

    print(f"\nROUTE: {result['route']}")

    print("\nAI ANSWER:")
    print(result["answer"])

    print()