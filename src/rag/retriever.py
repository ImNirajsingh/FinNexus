from pathlib import Path
from langchain_chroma import Chroma

try:
    from .embeddings import get_embedding_model
except ImportError:
    from embeddings import get_embedding_model

COLLECTION_NAME = "bank_transactions"

def load_vectorstore(persist_directory: str = "vectorstore/chroma"):
    persist_directory = Path(persist_directory)

    if not persist_directory.exists():
        raise FileNotFoundError(f"Vector store not found : {persist_directory}")

    embeddings = get_embedding_model()
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=str(persist_directory),
        embedding_function=embeddings,
    )
    return vectorstore


def search_transactions(query: str, k: int = 5, persist_directory: str = "vectorstore/chroma"):
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    vectorstore = load_vectorstore(persist_directory=persist_directory)

    results = vectorstore.similarity_search(query=query, k=k)

    return results

def get_vectorstore_count(persist_directory: str = "vectorstore/chroma"):
    vectorstore = load_vectorstore(persist_directory=persist_directory)

    return vectorstore._collection.count()