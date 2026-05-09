# config.py
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

# RAG config
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"
LLM_TEMPERATURE = 0.2
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RETRIEVAL_K = 4
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
CHROMA_PERSIST_DIR = ".chroma/rag-store"
CHUNKS_DB_PATH = "chunks.db"