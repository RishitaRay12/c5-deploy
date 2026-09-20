import tempfile
import re
from fastapi import UploadFile, HTTPException
from schema import UploadResponse
import logging
import os
from parse_tables import parse_pdf_tables
from app.vector_store import add_text_chunks, get_vector_store

vector_store = get_vector_store()

logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 100) -> list[str]:
    if not text or not text.strip():
        return []

    words = re.findall(r"\S+", text)
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        if end == len(words):
            break
        start = max(start + chunk_size - chunk_overlap, start + 1)

    return chunks


async def _process_uploaded_files(files: list[UploadFile]) -> list[UploadResponse]:
    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded.")

    results: list[UploadResponse] = []
    supported_extensions = {".pdf", ".txt", ".md", ".csv", ".json"}

    for uploaded_file in files:
        filename = uploaded_file.filename or "uploaded_file"
        extension = os.path.splitext(filename)[1].lower()

        if extension not in supported_extensions:
            logger.info("Skipping unsupported file: %s", filename)
            continue

        try:
            payload = await uploaded_file.read()
            if extension == ".pdf":
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                    temp_file.write(payload)
                    temp_path = temp_file.name

                try:
                    full_text, dataframes = parse_pdf_tables(temp_path)
                    text_chunks = chunk_text(full_text)
                    table_chunks = [df.to_markdown(index=False) for df in dataframes]
                    documents_added = add_text_chunks(vector_store, filename, text_chunks, "text")
                    documents_added += add_text_chunks(vector_store, filename, table_chunks, "table")
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            else:
                content = payload.decode("utf-8", errors="ignore")
                documents_added = add_text_chunks(vector_store, filename, chunk_text(content), "text")

            results.append(
                UploadResponse(
                    filename=filename,
                    status="success",
                    files_processed=1,
                    documents_added=documents_added,
                )
            )
        except Exception as exc:
            logger.exception("Failed to process uploaded file: %s", filename)
            results.append(
                UploadResponse(
                    filename=filename,
                    status=f"failed: {str(exc)}",
                    files_processed=1,
                    documents_added=0,
                )
            )

    if not results:
        raise HTTPException(
            status_code=400,
            detail="No supported files were received. Supported types: .pdf, .txt, .md, .csv, .json",
        )

    return results