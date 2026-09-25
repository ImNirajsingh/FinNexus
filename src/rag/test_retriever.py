from retriever import search_transactions


queries = [
    "transactions involving Akhilesh Yadav",
    "payments related to food",
    "transactions involving BharatPe",
    "large outgoing payments",
]


for query in queries:

    print()
    print("=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)

    results = search_transactions(
        query=query,
        k=5,
    )

    for i, document in enumerate(results, start=1):

        print()
        print(f"RESULT {i}")
        print("-" * 80)

        print(document.page_content)

        print()
        print("Metadata:")
        print(document.metadata)