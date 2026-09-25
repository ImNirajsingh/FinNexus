from retriever import load_vectorstore, get_vectorstore_count

print("=" * 70)
print("CHROMADB DIAGNOSTIC")
print("=" * 70)

vectorstore = load_vectorstore()
count = get_vectorstore_count()
print(f"Documents in ChromaDB: {count:,}")

print()
print("=" * 70)
print("COLLECTION INFORMATION")
print("=" * 70)
print(vectorstore._collection)

print()
print("=" * 70)
print("DIRECT DATABASE CHECK")
print("=" * 70)

data = vectorstore._collection.get(limit=3, include=["documents", "metadatas"])
print(f"Documents returned: {len(data['documents'])}")
for i, document in enumerate(data["documents"], start=1):
    print()
    print(f"DOCUMENT {i}")
    print("-" * 70)
    print(document)
    print()
    print("Metadata:")
    print(data["metadatas"][i - 1])