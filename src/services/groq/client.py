import logging

from langchain_groq import ChatGroq

from src.config import settings

logger = logging.getLogger(__name__)


class GroqService:
    """LangChain-based Groq LLM client."""

    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=0.1,
            max_tokens=1024,
        )

    async def generate(self, prompt: str) -> str:
        """
        Generate a response from Groq LLM.

        Args:
            prompt: Full prompt string

        Returns:
            Generated text response
        """
        try:
            response = await self.llm.ainvoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            raise


groq_service = GroqService()
