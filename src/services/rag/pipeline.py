import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from src.services.cache.redis import cache_service
from src.services.embeddings.jina import jina_service
from src.services.groq.client import groq_service
from src.services.qdrant.client import qdrant_service
from src.services.search.keyword import keyword_search_service

logger = logging.getLogger(__name__)

RAG_PROMPT_TEMPLATE = """You are a helpful research assistant that answers questions about academic papers.

Use the following context from research papers to answer the question.
If the context does not contain enough information to answer the question, say so honestly.
Always cite the paper titles you used in your answer.

Context:
{context}

Question: {question}

Answer:"""


class RAGPipeline:
    """Orchestrates retrieval and generation for RAG with caching."""

    async def ask(
        self,
        question: str,
        session: Session,
        top_k: int = 5,
        mode: str = "hybrid",
    ) -> Dict[str, Any]:
        """Answer a question using RAG with caching."""

        # check cache first
        cached = cache_service.get(question, mode)
        if cached:
            cached["from_cache"] = True
            return cached

        # retrieve chunks
        chunks = await self._retrieve(question, session, top_k, mode)

        if not chunks:
            return {
                "answer": "I could not find any relevant papers to answer your question.",
                "sources": [],
                "chunks_used": 0,
                "from_cache": False,
            }

        # build context and prompt
        context = self._build_context(chunks)
        prompt = RAG_PROMPT_TEMPLATE.format(
            context=context,
            question=question,
        )

        # generate answer
        answer = await groq_service.generate(prompt)

        # build result
        sources = self._extract_sources(chunks)
        result = {
            "answer": answer,
            "sources": sources,
            "chunks_used": len(chunks),
            "from_cache": False,
        }

        # cache result
        cache_service.set(question, mode, result)

        return result

    async def _retrieve(
        self,
        question: str,
        session: Session,
        top_k: int,
        mode: str,
    ) -> List[Dict]:
        """Retrieve relevant chunks using specified search mode."""

        if mode == "keyword":
            results = keyword_search_service.search(session, question, top_k)
            return [{"text": r["abstract"], **r} for r in results]

        query_vector = await jina_service.embed_query(question)

        hits = qdrant_service.client.query_points(
            collection_name=qdrant_service.collection_name,
            query=query_vector,
            limit=top_k,
        ).points

        chunks = [
            {
                "text": hit.payload["text"],
                "arxiv_id": hit.payload["arxiv_id"],
                "title": hit.payload["title"],
                "authors": hit.payload["authors"],
                "score": hit.score,
            }
            for hit in hits
        ]

        if mode == "hybrid":
            keyword_results = keyword_search_service.search(session, question, top_k)
            seen_ids = {c["arxiv_id"] for c in chunks}
            for r in keyword_results:
                if r["arxiv_id"] not in seen_ids:
                    chunks.append(
                        {
                            "text": r["abstract"],
                            "arxiv_id": r["arxiv_id"],
                            "title": r["title"],
                            "authors": r["authors"],
                            "score": r["score"],
                        }
                    )

        return chunks[:top_k]

    def _build_context(self, chunks: List[Dict]) -> str:
        """Format chunks into context string."""
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[{i}] Paper: {chunk['title']}\n"
                f"Authors: {', '.join(chunk['authors']) if chunk['authors'] else 'Unknown'}\n"
                f"Content: {chunk['text'][:1000]}\n"
            )
        return "\n---\n".join(context_parts)

    def _extract_sources(self, chunks: List[Dict]) -> List[Dict]:
        """Extract unique paper sources from chunks."""
        seen = {}
        for chunk in chunks:
            aid = chunk["arxiv_id"]
            if aid not in seen:
                seen[aid] = {
                    "arxiv_id": aid,
                    "title": chunk["title"],
                    "authors": chunk["authors"],
                }
        return list(seen.values())


rag_pipeline = RAGPipeline()
