from route_executor import execute_query


test_queries = [
    "How much did I spend in March?",
    "Show transactions involving Akhilesh Yadav",
    "What unusual transactions occurred?",
    "Why was my spending higher in March?",
]


for query in test_queries:

    print("=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)

    result = execute_query(query)

    print(f"ROUTE: {result['route']}")

    if result["route"] == "analytics":

        print("\nFinancial Summary:")
        print(result["financial_summary"])

        print("\nMonthly Summary:")
        print(result["monthly_summary"])

    elif result["route"] == "rag":

        print("\nRetrieved Transactions:")

        for i, transaction in enumerate(
            result["results"],
            start=1,
        ):
            print(f"\n--- Result {i} ---")
            print(transaction["content"])

    elif result["route"] == "ml":

        print("\nAnomalies:")

        for anomaly in result["anomalies"][:10]:
            print(anomaly)

    elif result["route"] == "hybrid":

        print("\nFinancial Summary:")
        print(result["financial_summary"])

        print("\nMonthly Summary:")
        print(result["monthly_summary"])

        print("\nTop Anomalies:")

        for anomaly in result["anomalies"]:
            print(anomaly)