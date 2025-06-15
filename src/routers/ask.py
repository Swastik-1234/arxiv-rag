from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.rag.pipeline import rag_pipeline

router = APIRouter(prefix="/api/v1", tags=["ask"])


@router.post("/ask")
async def ask(
    query: str = Query(..., description="Your question about the papers"),
    mode: str = Query("hybrid", description="Search mode: hybrid, semantic, keyword"),
    top_k: int = Query(5, ge=1, le=20, description="Number of chunks to retrieve"),
    db: Session = Depends(get_db),
):
    """
    Ask a question and get an answer based on ingested papers.
    """
    result = await rag_pipeline.ask(
        question=query,
        session=db,
        top_k=top_k,
        mode=mode,
    )
    return {
        "query": query,
        "answer": result["answer"],
        "sources": result["sources"],
        "chunks_used": result["chunks_used"],
        "mode": mode,
    }
