import hashlib
import json
import logging
from typing import Optional

import redis

from src.config import settings

logger = logging.getLogger(__name__)

CACHE_TTL = 60 * 60 * 24  # 24 hours


class CacheService:
    """Redis cache service for RAG responses."""

    def __init__(self):
        try:
            self.client = redis.from_url(settings.redis_url)
            self.client.ping()
            logger.info("Redis cache connected")
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
            self.client = None

    def _make_key(self, question: str, mode: str) -> str:
        """Generate cache key from question and mode."""
        content = f"{question.lower().strip()}:{mode}"
        return f"rag:{hashlib.md5(content.encode()).hexdigest()}"

    def get(self, question: str, mode: str) -> Optional[dict]:
        """Get cached response for a question."""
        if not self.client:
            return None
        try:
            key = self._make_key(question, mode)
            value = self.client.get(key)
            if value:
                logger.info(f"Cache hit for: {question[:50]}")
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
            return None

    def set(self, question: str, mode: str, response: dict) -> None:
        """Cache a response for a question."""
        if not self.client:
            return
        try:
            key = self._make_key(question, mode)
            self.client.setex(key, CACHE_TTL, json.dumps(response))
            logger.info(f"Cached response for: {question[:50]}")
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")

    def health_check(self) -> bool:
        """Check if Redis is reachable."""
        try:
            return self.client.ping() if self.client else False
        except Exception:
            return False


cache_service = CacheService()
