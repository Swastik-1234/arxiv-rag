import logging
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class KeywordSearchService:
    """BM25 keyword search using PostgreSQL full-text search."""

    def search(
        self,
        session: Session,
        query: str,
        limit: int = 10,
        category: Optional[str] = None,
    ) -> List[dict]:
        """
        Search papers using PostgreSQL full-text search.

        Args:
            session: Database session
            query: Search query string
            limit: Max number of results
            category: Optional arXiv category filter (e.g. cs.AI)

        Returns:
            List of matching papers with relevance scores
        """
        if not query.strip():
            return []

        # build base query with ts_rank for BM25-like scoring
        sql = """
            SELECT
                arxiv_id,
                title,
                abstract,
                authors,
                categories,
                published_date,
                pdf_url,
                pdf_processed,
                ts_rank(
                    to_tsvector('english', title || ' ' || abstract),
                    plainto_tsquery('english', :query)
                ) AS score
            FROM papers
            WHERE
                to_tsvector('english', title || ' ' || abstract)
                @@ plainto_tsquery('english', :query)
        """

        params = {"query": query, "limit": limit}

        if category:
            sql += " AND :category = ANY(categories)"
            params["category"] = category

        sql += " ORDER BY score DESC LIMIT :limit"

        try:
            results = session.execute(text(sql), params).fetchall()

            papers = []
            for row in results:
                papers.append(
                    {
                        "arxiv_id": row.arxiv_id,
                        "title": row.title,
                        "abstract": row.abstract,
                        "authors": row.authors,
                        "categories": row.categories,
                        "published_date": str(row.published_date),
                        "pdf_url": row.pdf_url,
                        "score": float(row.score),
                    }
                )

            logger.info(f"Keyword search for '{query}' returned {len(papers)} results")
            return papers

        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []


keyword_search_service = KeywordSearchService()
