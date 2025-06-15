import logging
from typing import List

import httpx

from src.config import settings

logger = logging.getLogger(__name__)

JINA_API_URL = "https://api.jina.ai/v1/embeddings"


class JinaEmbeddingService:
    """Service for generating embeddings using Jina AI API."""

    def __init__(self):
        self.api_key = settings.jina_api_key
        self.model = settings.jina_embedding_model

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "input": texts,
            "task": "retrieval.passage",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    JINA_API_URL,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            embeddings = [item["embedding"] for item in data["data"]]
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings

        except Exception as e:
            logger.error(f"Jina embedding failed: {e}")
            raise

    async def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a single search query.

        Args:
            query: Search query string

        Returns:
            Embedding vector
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "input": [query],
            "task": "retrieval.query",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                JINA_API_URL,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return data["data"][0]["embedding"]


jina_service = JinaEmbeddingService()
