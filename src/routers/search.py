from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.search.keyword import keyword_search_service

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.get("/search")
def search_papers(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
    category: Optional[str] = Query(
        None, description="Filter by arXiv category e.g. cs.AI"
    ),
    db: Session = Depends(get_db),
):
    """
    Search papers using BM25 keyword search.
    """
    results = keyword_search_service.search(
        session=db,
        query=q,
        limit=limit,
        category=category,
    )

    return {
        "query": q,
        "total": len(results),
        "results": results,
    }
