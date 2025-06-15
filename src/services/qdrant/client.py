import logging

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from src.config import settings

logger = logging.getLogger(__name__)

VECTOR_SIZE = 1024  # jina-embeddings-v3 output size


class QdrantService:
    """Service for managing Qdrant vector store."""

    def __init__(self):
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )
        self.collection_name = settings.qdrant_collection_name

    def create_collection(self):
        """Create Qdrant collection if it doesn't exist."""
        existing = [c.name for c in self.client.get_collections().collections]

        if self.collection_name in existing:
            logger.info(f"Collection '{self.collection_name}' already exists")
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )
        logger.info(f"Created collection '{self.collection_name}'")

    def health_check(self) -> bool:
        """Check if Qdrant is reachable."""
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

    def get_collection_info(self) -> dict:
        """Get collection stats."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "status": str(info.status),
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {"error": str(e)}


qdrant_service = QdrantService()
