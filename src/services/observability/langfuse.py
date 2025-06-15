import logging
from typing import Any, Optional

from src.config import settings

logger = logging.getLogger(__name__)


class LangfuseService:
    """Langfuse v4 observability service."""

    def __init__(self):
        self.enabled = bool(
            settings.langfuse_public_key and settings.langfuse_secret_key
        )
        self.client = None

        if self.enabled:
            try:
                from langfuse import Langfuse

                self.client = Langfuse(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    host=settings.langfuse_host,
                )
                logger.info("Langfuse tracing enabled")
            except Exception as e:
                logger.warning(f"Langfuse init failed: {e}")
                self.enabled = False
        else:
            logger.info("Langfuse not configured — tracing disabled")

    def trace(self, name: str, input: dict) -> Optional[Any]:
        """Start a new trace."""
        if not self.enabled or not self.client:
            return None
        try:
            return self.client.start_observation(
                name=name,
                as_type="span",
                input=input,
            )
        except Exception as e:
            logger.warning(f"Langfuse trace failed: {e}")
            return None

    def span(self, trace: Any, name: str, input: dict) -> Optional[Any]:
        """Create a span."""
        if not self.enabled or not trace:
            return None
        try:
            return self.client.start_observation(
                name=name,
                as_type="span",
                input=input,
            )
        except Exception as e:
            logger.warning(f"Langfuse span failed: {e}")
            return None

    def end_span(self, span: Any, output: dict) -> None:
        """End a span with output."""
        if not self.enabled or not span:
            return
        try:
            span.update(output=output)
            span.end()
        except Exception as e:
            logger.warning(f"Langfuse end span failed: {e}")

    def end_trace(self, trace: Any, output: dict) -> None:
        """End a trace with output."""
        if not self.enabled or not trace:
            return
        try:
            trace.update(output=output)
            trace.end()
            self.client.flush()
        except Exception as e:
            logger.warning(f"Langfuse end trace failed: {e}")


langfuse_service = LangfuseService()
