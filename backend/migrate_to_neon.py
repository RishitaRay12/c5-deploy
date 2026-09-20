import json
import sqlite3
from pathlib import Path

import chromadb
from langchain_core.documents import Document
from psycopg.types.json import Jsonb

from app.config import settings
from app.vector_store import get_vector_store
from sql_data import init_postgres


TABLES = (
    "users",
    "vendors",
    "audit_logs",
    "retention_records",
    "compliance_reviews",
    "chat_messages",
)


def migrate_embeddings(chroma_path: Path) -> int:
    client = chromadb.PersistentClient(path=str(chroma_path))
    try:
        collection = client.get_collection(settings.VECTOR_COLLECTION_NAME)
    except Exception:
        return 0

    records = collection.get(include=["documents", "metadatas"])
    documents = records.get("documents") or []
    metadatas = records.get("metadatas") or []
    ids = records.get("ids") or []
    if not documents:
        return 0

    store = get_vector_store()
    store.add_documents(
        [Document(page_content=text, metadata=metadata or {}) for text, metadata in zip(documents, metadatas)],
        ids=ids,
    )
    return len(documents)


def main() -> None:
    if not settings.NEON_DB_URI:
        raise RuntimeError("NEON_DB_URI is required")

    source_path = Path(settings.DB_FILE)
    if not source_path.exists():
        raise FileNotFoundError(f"SQLite database not found: {source_path}")

    init_postgres()
    with sqlite3.connect(source_path) as source:
        source.row_factory = sqlite3.Row
        import psycopg

        with psycopg.connect(settings.NEON_DB_URI) as destination:
            for table in TABLES:
                rows = source.execute(f"SELECT * FROM {table}").fetchall()
                if not rows:
                    continue
                columns = [column[1] for column in source.execute(f"PRAGMA table_info({table})")]
                for row in rows:
                    insert_columns = [column for column in columns if column not in {"sources", "token_usage"}]
                    if table == "chat_messages":
                        insert_columns.extend(["sources", "token_usage"])
                    values = [row[column] for column in columns if column not in {"sources", "token_usage"}]
                    if table == "chat_messages":
                        values.extend([
                            Jsonb(json.loads(row["sources"] or "[]")) if "sources" in columns else Jsonb([]),
                            Jsonb(json.loads(row["token_usage"])) if "token_usage" in columns and row["token_usage"] else None,
                        ])
                    placeholders = ", ".join(["%s"] * len(values))
                    conflict_column = "username" if table == "users" else "id" if table == "chat_messages" else columns[0]
                    destination.execute(
                        f"INSERT INTO {table} ({', '.join(insert_columns)}) "
                        f"SELECT {placeholders} WHERE NOT EXISTS "
                        f"(SELECT 1 FROM {table} WHERE {conflict_column} = %s)",
                        [*values, row[conflict_column] if conflict_column in columns else row[columns[0]]],
                    )
                identity_column = {
                    "users": "id",
                    "vendors": "vendor_id",
                    "audit_logs": "log_id",
                    "retention_records": "record_id",
                    "compliance_reviews": "review_id",
                    "chat_messages": "id",
                }[table]
                destination.execute(
                    f"SELECT setval(pg_get_serial_sequence(%s, %s), COALESCE(MAX({identity_column}), 1), true) FROM {table}",
                    (table, identity_column),
                )

    count = migrate_embeddings(Path("chroma_db"))
    print(f"Migrated SQLite tables and {count} vector documents to Neon.")


if __name__ == "__main__":
    main()
