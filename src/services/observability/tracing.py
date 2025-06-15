import logging
import os

from src.config import settings

logger = logging.getLogger(__name__)


def setup_tracing():
    """Setup LangSmith tracing via environment variables."""
    if settings.langchain_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
        os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
        logger.info("LangSmith tracing enabled")
    else:
        logger.info("LangSmith not configured — tracing disabled")
