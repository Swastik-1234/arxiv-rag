import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.embeddings.jina import jina_service
from src.services.qdrant.client import qdrant_service
from src.services.search.keyword import keyword_search_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["hybrid-search"])


@router.post("/index")
async def trigger_indexing(db: Session = Depends(get_db)):
    """Trigger indexing of all unembedded papers into Qdrant."""
    from src.services.indexing.pipeline import indexing_pipeline

    result = await indexing_pipeline.index_all_unembedded(db)
    return result


@router.get("/hybrid-search")
async def hybrid_search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    category: Optional[str] = Query(None),
    mode: str = Query("hybrid", description="hybrid, semantic, keyword"),
    db: Session = Depends(get_db),
):
    """Hybrid search combining BM25 keyword + semantic vector search."""

    if mode == "keyword":
        results = keyword_search_service.search(db, q, limit, category)
        return {"query": q, "mode": mode, "total": len(results), "results": results}

    query_vector = await jina_service.embed_query(q)

    if mode == "semantic":
        hits = qdrant_service.client.query_points(
            collection_name=qdrant_service.collection_name,
            query=query_vector,
            limit=limit,
        ).points
        results = [
            {
                "arxiv_id": hit.payload["arxiv_id"],
                "title": hit.payload["title"],
                "text": hit.payload["text"],
                "authors": hit.payload["authors"],
                "categories": hit.payload["categories"],
                "score": hit.score,
            }
            for hit in hits
        ]
        return {"query": q, "mode": mode, "total": len(results), "results": results}

    # hybrid mode
    keyword_results = keyword_search_service.search(db, q, limit, category)
    semantic_hits = qdrant_service.client.query_points(
        collection_name=qdrant_service.collection_name,
        query=query_vector,
        limit=limit,
    ).points

    seen = {}
    for hit in semantic_hits:
        aid = hit.payload["arxiv_id"]
        seen[aid] = {
            "arxiv_id": aid,
            "title": hit.payload["title"],
            "text": hit.payload["text"],
            "authors": hit.payload["authors"],
            "categories": hit.payload["categories"],
            "score": hit.score,
            "match_type": "semantic",
        }

    for paper in keyword_results:
        aid = paper["arxiv_id"]
        if aid not in seen:
            seen[aid] = {**paper, "match_type": "keyword"}
        else:
            seen[aid]["score"] = (seen[aid]["score"] + paper["score"]) / 2
            seen[aid]["match_type"] = "hybrid"

    results = sorted(seen.values(), key=lambda x: x["score"], reverse=True)[:limit]
    return {"query": q, "mode": mode, "total": len(results), "results": results}
