from documents import (
    load_transactions,
    create_transaction_documents,
)


DATA_PATH = "data/processed/cleaned_transactions.csv"


print("Loading transactions...")

df = load_transactions(DATA_PATH)

print(f"Transactions loaded: {len(df):,}")


print("Creating RAG documents...")

documents = create_transaction_documents(df)

print(f"Documents created: {len(documents):,}")


print()
print("=" * 70)
print("FIRST DOCUMENT")
print("=" * 70)

print(documents[0].page_content)


print()
print("=" * 70)
print("FIRST DOCUMENT METADATA")
print("=" * 70)

print(documents[0].metadata)


print()
print("=" * 70)
print("DOCUMENT VALIDATION")
print("=" * 70)

print(
    "Transactions:",
    len(df)
)

print(
    "Documents:",
    len(documents)
)

print(
    "Match:",
    len(df) == len(documents)
)