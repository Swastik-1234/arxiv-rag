from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers import ask, health, hybrid_search, search
from src.services.observability.tracing import setup_tracing


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting arXiv RAG API...")
    setup_tracing()
    from src.services.qdrant.client import qdrant_service

    qdrant_service.create_collection()
    yield
    print("Shutting down arXiv RAG API...")


app = FastAPI(
    title="arXiv Paper Curator",
    description="Production RAG system for academic paper search and Q&A",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── routers ──────────────────────────────
app.include_router(health.router, tags=["health"])
app.include_router(search.router)
app.include_router(hybrid_search.router)
app.include_router(ask.router)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
