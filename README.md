# Student Management System + Conversational RAG

A Python web application combining **student management** (MySQL-backed CRUD with a natural-language chatbot) and **Conversational RAG Q&A over PDFs** (LangChain + Groq + ChromaDB), all in one Streamlit app.

---

## Features

### Student Management
- **Authentication** — Role-based login for admins and regular users
- **Admin Dashboard** — Full CRUD operations through a sidebar menu
- **Bulk Import** — Upload a CSV file to insert multiple students at once
- **Chatbot Interface** — Natural language commands to query and manage student data
- **Grade Validation** — Supports grades: `A+`, `A`, `B+`, `B`, `C+`, `C`, `D`, `F`

### Document Q&A (RAG)
- **PDF Upload & Ingestion** — multiple PDFs at once
- **Local embeddings** — `all-MiniLM-L6-v2` runs locally, no API key
- **Persistent vector store** — ChromaDB on disk (`.chroma/rag-store`)
- **Raw chunks DB** — every chunk also saved to a SQLite file (`chunks.db`) for inspection
- **History-aware retrieval** — follow-up questions resolved using chat history
- **Per-session memory** — conversations isolated by Session ID
- **Retrieved chunks display** — every answer shows the source chunks used

---

## Project Structure

```
├── app.py                  # Streamlit UI (login + admin + user + Document Q&A)
├── chatbot.py              # Chatbot facade (legacy commands + ask() for RAG)
├── CRUD.py                 # MySQL CRUD operations
├── database.py             # MySQL connection
├── config.py               # Loads DB + RAG config from .env
├── auth.py                 # Login & role checking
├── student.py              # Student class
├── main.py                 # CLI entry point (testing)
│
├── engines/                # Strategy pattern — pluggable chat engines
│   ├── base.py             #   ChatEngine Protocol
│   ├── simple_faq.py       #   Legacy FAQ engine (Project 1)
│   └── rag_engine.py       #   RAG engine (wraps LangChain chain)
│
├── rag/
│   ├── ingest.py           # PDF → chunks → embeddings → Chroma + chunks.db
│   └── pipeline.py         # LCEL chain + history wiring
│
├── .streamlit/
│   └── config.toml         # Disables noisy file watcher
│
├── students.csv            # Sample bulk-import data
├── admins.json             # Admin credentials
├── users.json              # User credentials
├── .env.example            # Environment template
└── requirements.txt        # Python dependencies
```

---

## Setup

### 1. Clone & create a venv
```bash
git clone <your-repo-url>
cd projectone
python -m venv venv
venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
Copy `.env.example` to `.env` and fill in:

```
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=student_db
DB_HOST=localhost
DB_PORT=3306

GROQ_API_KEY="your-groq-key"
```

Get a **free** Groq key at [console.groq.com/keys](https://console.groq.com/keys) (no credit card required).

### 4. Create the MySQL schema
```sql
CREATE DATABASE IF NOT EXISTS student_db;
USE student_db;

CREATE TABLE IF NOT EXISTS students (
    id    INT AUTO_INCREMENT PRIMARY KEY,
    name  VARCHAR(100),
    age   INT,
    grade VARCHAR(5)
);
```

### 5. Run
```bash
streamlit run app.py
```

> The first time you process PDFs, the embedding model (`all-MiniLM-L6-v2`, ~90 MB) downloads automatically and is cached locally.

---

## Chatbot Commands (Student Management)

| Command | Role | Description |
|---|---|---|
| `all students` | All | View all students |
| `student id 3` | All | Find student by ID |
| `search name Ali` | All | Search students by name |
| `grade A+` | All | Filter by grade |
| `age 22` | All | Filter by age |
| `top students` | All | List students sorted by grade |
| `passing students` | All | List non-failing students |
| `count students` | All | Total number of students |
| `average age` | All | Average age of all students |
| `add student Ali 20 A+` | Admin | Add a new student |
| `delete student 3` | Admin | Delete student by ID |
| `update student 3 grade B+` | Admin | Update a student's grade |

---

# Technical Description

## Architecture — Strategy Pattern

The app uses the **Strategy Pattern** so a single `Chatbot` facade can switch between completely different conversational engines without the UI changing:

```
                    ┌─────────────────────┐
                    │    Streamlit UI     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Chatbot facade    │   chatbot.py
                    │  - respond()        │   — student NL commands
                    │  - ask()            │   — delegates to engine.answer()
                    └──────────┬──────────┘
                               │ injected
                    ┌──────────▼──────────┐
                    │  ChatEngine (proto) │   engines/base.py
                    │   answer(sid, q)    │
                    │   get_history(sid)  │
                    └──────────┬──────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
       ┌────────▼────────┐          ┌─────────▼────────┐
       │ SimpleFAQEngine │          │    RagEngine     │
       │ (legacy P1)     │          │ (LangChain RAG)  │
       └─────────────────┘          └──────────────────┘
```

The UI imports the facade only — it never touches LangChain internals. New engines can be added without rewriting the UI.

---

## RAG Pipeline — Step by Step

When a user uploads PDFs and asks a question, the following happens:

### 1. Ingestion (`rag/ingest.py`)
```
PDF files
   │  PyPDFLoader
   ▼
LangChain Documents (one per page)
   │  RecursiveCharacterTextSplitter (size=1000, overlap=200)
   ▼
Chunks (Documents with metadata: source, page, etc.)
   │
   ├──► chunks.db          (SQLite — raw text + metadata, for inspection)
   │
   └──► HuggingFaceEmbeddings(all-MiniLM-L6-v2)
            │
            ▼
       384-dim vectors
            │
            ▼
       ChromaDB (.chroma/rag-store)   — persisted to disk
```

The embedding model runs **fully locally** — no API call, no key. Chroma uses an internal SQLite file (`chroma.sqlite3`) inside the persist directory to store embeddings + metadata. We additionally write a flat `chunks.db` so the raw chunks can be inspected with any SQLite viewer.

### 2. Query Time (`rag/pipeline.py`)

For every question, an LCEL (LangChain Expression Language) chain runs:

```
User question + chat_history
        │
        ▼
┌───────────────────────────┐
│  Step 1: Contextualize    │
│  IF chat_history exists:  │
│    LLM rewrites question  │
│    into standalone form   │
│  ELSE: use as-is          │
└───────────┬───────────────┘
            ▼
   "standalone question"
            │
            ▼
┌───────────────────────────┐
│  Step 2: Retrieve         │
│  Chroma similarity search │
│  top-K (default K=4)      │
└───────────┬───────────────┘
            ▼
     [doc1, doc2, doc3, doc4]
            │
            ▼
┌───────────────────────────┐
│  Step 3: Generate         │
│  System prompt + context  │
│    + chat_history         │
│    + user question        │
│  → Groq llama-3.3-70b     │
└───────────┬───────────────┘
            ▼
        Final answer
```

**Why contextualize first?** A follow-up like *"and what about the second one?"* makes no sense in isolation. The LLM rewrites it into a self-contained query (e.g. *"What does the document say about the second method described in section 2?"*) before retrieval — without this step, the vector search would return irrelevant chunks.

### 3. Output

The chain returns a dict:
```python
{
  "answer": "Based on the document, ...",
  "docs":   [Document, Document, Document, Document]
}
```

The UI displays the answer plus an **expandable "Retrieved N chunks"** panel showing the exact chunks used — page number, source file, full text.

---

## Chat History — How It Works

### The Problem
RAG over a single message is easy. RAG over a *conversation* needs three things:
1. Each user gets their own thread (no cross-pollution between users).
2. Follow-up questions must be resolved relative to past turns.
3. History should not pollute the vector search itself.

### The Solution

**Per-session in-memory store** (`rag/pipeline.py`):
```python
store: dict[str, ChatMessageHistory] = {}

def _get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]
```

`ChatMessageHistory` is a list of `HumanMessage` / `AIMessage` objects.

**`RunnableWithMessageHistory`** wraps the chain and automatically:
- Injects the session's history under the `chat_history` key on each invocation.
- Appends the new user message + AI answer to the session's history after the response.

```python
chain_with_history = RunnableWithMessageHistory(
    rag_chain,
    _get_session_history,
    input_messages_key="input",         # which key holds the new user question
    history_messages_key="chat_history",# which key gets the past messages injected
    output_messages_key="answer",       # which key contains the AI's response
)
```

### What Each Layer Stores

| Layer | What | Lifetime |
|---|---|---|
| `RagEngine.history_store` | `ChatMessageHistory` per session ID — full LangChain message objects | Process lifetime |
| `st.session_state.rag_messages` | Display-friendly list `[{role, content, docs}]` | Browser session |
| `chunks.db` (SQLite) | The raw text chunks themselves (not chat history) | Persisted to disk |
| ChromaDB (`.chroma/rag-store`) | Embeddings + chunk metadata | Persisted to disk |

So there are effectively **two parallel histories**:
- LangChain's `ChatMessageHistory` — used by the LLM to contextualize follow-ups
- Streamlit's `rag_messages` — used by the UI to render the chat transcript with retrieved chunks

They're kept in sync because both are appended to in the same code path.

### Why Session ID?

Multiple users (or multiple browser tabs) hitting the same backend would share the `store` dict. The Session ID keys ensure:
- User A's questions never appear in User B's contextualization step.
- The same user can intentionally start a fresh conversation by changing their Session ID.

---

## Tech Stack

| Layer | Tool |
|---|---|
| UI | Streamlit |
| Auth & DB | MySQL via `mysql-connector-python` |
| LLM | Groq `llama-3.3-70b-versatile` (free tier) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local) |
| Vector store | ChromaDB (persisted to disk) |
| Chunk storage | SQLite (`chunks.db`) |
| Orchestration | LangChain LCEL + `RunnableWithMessageHistory` |
| PDF parsing | `pypdf` via `PyPDFLoader` |
| Splitter | `RecursiveCharacterTextSplitter` |

---

## Tunables (`config.py`)

```python
GROQ_MODEL         = "llama-3.3-70b-versatile"
LLM_TEMPERATURE    = 0.2
EMBED_MODEL        = "sentence-transformers/all-MiniLM-L6-v2"
RETRIEVAL_K        = 4         # top-K chunks per query
CHUNK_SIZE         = 1000      # characters per chunk
CHUNK_OVERLAP      = 200       # overlap between consecutive chunks
CHROMA_PERSIST_DIR = ".chroma/rag-store"
CHUNKS_DB_PATH     = "chunks.db"
```
