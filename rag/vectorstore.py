import chromadb
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document

PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "papers"
EMBED_MODEL = "nomic-embed-text"


def get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(model=EMBED_MODEL)


def build_vectorstore(docs: list[Document]) -> Chroma:
    return Chroma.from_documents(
        documents=docs,
        embedding=get_embeddings(),
        persist_directory=PERSIST_DIR,
        collection_name=COLLECTION_NAME,
    )


def load_vectorstore() -> Chroma:
    return Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=get_embeddings(),
        collection_name=COLLECTION_NAME,
    )


def collection_exists() -> bool:
    try:
        client = chromadb.PersistentClient(path=PERSIST_DIR)
        col = client.get_collection(COLLECTION_NAME)
        return col.count() > 0
    except Exception:
        return False


def clear_vectorstore() -> None:
    try:
        client = chromadb.PersistentClient(path=PERSIST_DIR)
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
