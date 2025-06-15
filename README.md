# arXiv Paper Curator — Production RAG System

![arXiv Paper Curator Demo](static/demo.png)

A production-grade Retrieval-Augmented Generation (RAG) system that automatically ingests arXiv research papers daily and answers questions about them using hybrid search and a Groq LLM.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![LangChain](https://img.shields.io/badge/LangChain-0.2-orange)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)

---

## Architecture

```
arXiv API → Airflow DAG → PDF Extraction → PostgreSQL
                                              ↓
                                    Jina AI Embeddings
                                              ↓
                                           Qdrant
                                              ↓
User → Gradio UI → FastAPI → Hybrid Search → Groq LLM → Answer
                                    ↑
                               Redis Cache
                                    ↑
                             LangSmith Tracing
```

---

## Stack

| Component | Technology |
|---|---|
| **Orchestration** | Apache Airflow |
| **Vector Store** | Qdrant |
| **Metadata DB** | PostgreSQL |
| **Embeddings** | Jina AI (`jina-embeddings-v3`) |
| **LLM** | Groq (`llama-3.1-8b-instant`) |
| **Retrieval** | LangChain (Hybrid: BM25 + Semantic) |
| **Caching** | Redis |
| **Observability** | LangSmith |
| **API** | FastAPI |
| **UI** | Gradio |

---

## Features

- **Daily paper ingestion** — Airflow DAG fetches latest arXiv papers (cs.AI, cs.LG, cs.CL) every weekday
- **PDF text extraction** — PyMuPDF extracts full text from downloaded PDFs
- **Hybrid search** — Combines BM25 keyword search with semantic vector search for best results
- **RAG pipeline** — Retrieves relevant chunks and passes them to Groq LLM for answer generation
- **Redis caching** — Identical queries return cached answers in ~10ms instead of 1-2 seconds
- **LangSmith tracing** — Every LLM call and retrieval is traced for monitoring
- **Gradio UI** — Clean chat interface for asking questions

---

## Project Structure

```
arxiv-rag/
├── src/
│   ├── routers/              # FastAPI endpoints (health, search, ask, hybrid-search)
│   ├── services/
│   │   ├── arxiv/            # arXiv API client + PDF parser
│   │   ├── embeddings/       # Jina AI embedding service
│   │   ├── groq/             # Groq LLM client
│   │   ├── indexing/         # Chunker + indexing pipeline
│   │   ├── observability/    # LangSmith tracing
│   │   ├── cache/            # Redis cache service
│   │   ├── qdrant/           # Qdrant vector store client
│   │   ├── rag/              # RAG pipeline orchestrator
│   │   └── search/           # BM25 keyword search
│   ├── models/               # SQLAlchemy DB models
│   ├── schemas/              # Pydantic schemas
│   ├── config.py             # Environment config
│   ├── database.py           # DB connection
│   └── main.py               # FastAPI app entry point
├── airflow/
│   ├── dags/
│   │   └── arxiv_ingestion.py  # Daily ingestion DAG
│   └── Dockerfile
├── compose.yml               # Docker Compose stack
├── Dockerfile                # FastAPI app image
├── gradio_launcher.py        # Gradio UI
├── pyproject.toml
└── .env.example
```

---

## Quick Start

### Prerequisites

- Docker Desktop (Mac/Linux) or Docker Desktop with WSL2 (Windows) — only Docker is required to run the full stack
- Python 3.12+ (only needed if you want to run tests/lint locally outside Docker)
- API keys: [Groq](https://console.groq.com/keys) (free), [Jina AI](https://jina.ai/embeddings) (free). [LangSmith](https://smith.langchain.com) is optional.

### 1. Clone and configure

```bash
git clone <this-repo-url>
cd arxiv-rag-master
cp .env.example .env
```

Edit `.env` and fill in your API keys:

```env
GROQ_API_KEY=gsk_...
JINA_API_KEY=jina_...
```

Generate the two required secrets and paste them into `.env`:

```bash
# AIRFLOW_FERNET_KEY
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# AIRFLOW_SECRET_KEY
openssl rand -hex 30
```

(`LANGFUSE_NEXTAUTH_SECRET` and `LANGFUSE_SALT` already have placeholder values in `.env.example` — fine for local use, but you can regenerate them the same way with `openssl rand -base64 32`.)

### 2. Start infrastructure

```bash
docker compose up -d postgres qdrant redis langfuse-db langfuse
```

Wait ~30s, then open **http://localhost:3000**, sign up (any email/password — it's local only), create a project, and copy its **Public Key** and **Secret Key** into `.env` as `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY`. (Optional — the app runs fine without this, tracing just stays disabled.)

### 3. Start Airflow

```bash
docker compose up -d airflow
```

First boot runs `airflow db migrate` and creates the admin user — wait ~1-2 minutes, then check `docker compose logs -f airflow` until you see "Starting Airflow webserver and scheduler...".

### 4. Start the FastAPI app

```bash
docker compose up -d --build app
```

### 5. Ingest papers

- Open Airflow at **http://localhost:8080** (login: whatever you set for `AIRFLOW_ADMIN_USER` / `AIRFLOW_ADMIN_PASSWORD`, default `admin`/`admin`)
- Trigger the `arxiv_paper_ingestion` DAG
- Wait for it to complete (fetches papers, downloads + parses PDFs, stores in Postgres)

### 6. Index papers into Qdrant

```bash
curl -X POST http://localhost:8000/api/v1/index
```

### 7. Launch the Gradio UI

The `app` container already exposes port 7861, but the bundled Gradio process isn't started by the Docker image — run it from your host:

```bash
pip install gradio httpx
python gradio_launcher.py
```

Open **http://localhost:7861** and start asking questions!

### Stopping everything

```bash
make stop      # or: docker compose down
```

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/api/v1/search` | GET | BM25 keyword search |
| `/api/v1/hybrid-search` | GET | Hybrid search (BM25 + semantic) |
| `/api/v1/ask` | POST | Ask a question (RAG) |
| `/api/v1/index` | POST | Index unembedded papers into Qdrant |

Full API docs at **http://localhost:8000/docs**

---

## Service URLs

| Service | URL |
|---|---|
| Gradio UI | http://localhost:7861 |
| API Docs | http://localhost:8000/docs |
| Airflow | http://localhost:8080 |
| Langfuse | http://localhost:3000 |
| Qdrant Dashboard | http://localhost:6333/dashboard |
| Postgres (host access) | localhost:5433 (mapped from container's 5432 to avoid clashing with a local Postgres install) |

---

## Environment Variables

See `.env.example` for all required variables. Key ones:

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key for LLM |
| `JINA_API_KEY` | Jina AI key for embeddings |
| `LANGCHAIN_API_KEY` | LangSmith key for tracing |
| `ARXIV_CATEGORIES` | Comma-separated arXiv categories |
| `ARXIV_MAX_RESULTS` | Papers per category per sync |

---

## License

MIT
