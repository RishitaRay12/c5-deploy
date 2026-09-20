from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_postgres import PGVector
from sentence_transformers import SentenceTransformer

from app.config import settings


class SentenceTransformerEmbeddings(Embeddings):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, normalize_embeddings=True).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.model.encode(text, normalize_embeddings=True).tolist()


_embeddings = SentenceTransformerEmbeddings()


def get_vector_store() -> PGVector:
    if not settings.NEON_DB_URI:
        raise RuntimeError("NEON_DB_URI is required for the PostgreSQL vector store")
    return PGVector(
        embeddings=_embeddings,
        connection=settings.NEON_SQLALCHEMY_URI,
        collection_name=settings.VECTOR_COLLECTION_NAME,
        embedding_length=384,
        use_jsonb=True,
    )


def add_text_chunks(
    store: PGVector,
    filename: str,
    chunks: list[str],
    chunk_type: str,
) -> int:
    documents = [
        Document(
            page_content=chunk,
            metadata={"source": filename, "chunk_index": index, "type": chunk_type},
        )
        for index, chunk in enumerate(chunks)
        if chunk and chunk.strip()
    ]
    if documents:
        store.add_documents(
            documents,
            ids=[f"{filename}_chunk_{index}" for index, document in enumerate(documents)],
        )
    return len(documents)
