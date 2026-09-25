from documents import (
    load_transactions,
    create_transaction_documents,
)

from vectorstore import create_vectorstore


DATA_PATH = "data/processed/cleaned_transactions.csv"
VECTORSTORE_PATH = "vectorstore/chroma"


# --------------------------------------------------
# Load transactions
# --------------------------------------------------

print("Loading transactions...")

df = load_transactions(DATA_PATH)

print(f"Transactions loaded: {len(df):,}")


# --------------------------------------------------
# Create documents
# --------------------------------------------------

print("Creating documents...")

documents = create_transaction_documents(df)

print(f"Documents created: {len(documents):,}")


# --------------------------------------------------
# Create vector store
# --------------------------------------------------

print("Creating ChromaDB vector store...")
print("Embedding documents...")

vectorstore = create_vectorstore(
    documents=documents,
    persist_directory=VECTORSTORE_PATH,
)

print()
print("=" * 70)
print("VECTOR STORE CREATED")
print("=" * 70)

print(f"Documents indexed: {len(documents):,}")
print(f"Vector store path : {VECTORSTORE_PATH}")
print("Collection        : bank_transactions")