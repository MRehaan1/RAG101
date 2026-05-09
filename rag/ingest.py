import os
import sqlite3
import tempfile
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from config import EMBED_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, CHROMA_PERSIST_DIR, CHUNKS_DB_PATH


def _get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=EMBED_MODEL)


def _save_chunks_to_db(chunks: list) -> None:
    """Persist raw text chunks into chunks.db (SQLite)."""
    con = sqlite3.connect(CHUNKS_DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            source      TEXT,
            page        INTEGER,
            chunk_index INTEGER,
            content     TEXT
        )
    """)
    con.executemany(
        "INSERT INTO chunks (source, page, chunk_index, content) VALUES (?, ?, ?, ?)",
        [
            (
                chunk.metadata.get("source", ""),
                chunk.metadata.get("page", 0),
                idx,
                chunk.page_content,
            )
            for idx, chunk in enumerate(chunks)
        ],
    )
    con.commit()
    con.close()


def ingest_pdfs(uploaded_files) -> Chroma:
    """Load uploaded PDFs, chunk, embed, persist in Chroma and chunks.db. Returns the vector store."""
    embeddings = _get_embeddings()
    all_docs = []

    for uploaded_file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        try:
            loader = PyPDFLoader(tmp_path)
            all_docs.extend(loader.load())
        finally:
            os.unlink(tmp_path)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(all_docs)

    _save_chunks_to_db(chunks)

    return Chroma.from_documents(
        chunks,
        embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
    )


def load_vectorstore() -> Chroma:
    """Load an existing persisted Chroma store from disk."""
    return Chroma(
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=_get_embeddings(),
    )
