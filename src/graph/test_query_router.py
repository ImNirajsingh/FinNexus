from query_router import route_query


test_queries = [
    "How much did I spend in March?",
    "What was my total income?",
    "What was my largest expense?",
    "How many transactions did I make?",

    "Show transactions involving Akhilesh Yadav",
    "Find payments related to BharatPe",
    "Show transactions involving Swiggy",

    "What unusual transactions occurred?",
    "Show me anomalous transactions",

    "Why was my spending higher in March?",
    "Why did my expenses increase?",
    "What are my major recurring expenses?",
]


for query in test_queries:

    route = route_query(query)

    print(f"QUERY : {query}")
    print(f"ROUTE : {route.value}")
    print("-" * 70)