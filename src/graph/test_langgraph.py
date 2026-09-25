from financial_graph import financial_graph


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

    result = financial_graph.invoke({
        "query": query
    })

    print("\nROUTE:")
    print(result["route"])

    print("\nAI ANSWER:")
    print(result["answer"])

    print()