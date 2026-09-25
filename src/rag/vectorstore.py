from pathlib import Path
from langchain_chroma import Chroma
from embeddings import get_embedding_model


def create_vectorstore(documents, persist_directory: str = "vectorstore/chroma"):
    persist_directory = Path(persist_directory)
    persist_directory.mkdir(parents = True, exist_ok = True)

    embeddings = get_embedding_model()

    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name="bank_transactions",
        persist_directory=str(persist_directory),
    )
    return vectorstore