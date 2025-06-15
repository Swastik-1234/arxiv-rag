from datetime import datetime

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def root():
    return {
        "message": "arXiv Paper Curator RAG API",
        "docs": "/docs",
        "health": "/health",
    }


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "arxiv-rag-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }
