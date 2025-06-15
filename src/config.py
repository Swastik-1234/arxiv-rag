from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # PostgreSQL
    postgres_user: str = "arxiv_user"
    postgres_password: str = "arxiv_password"
    postgres_db: str = "arxiv_db"
    database_url: str = (
        "postgresql+asyncpg://arxiv_user:arxiv_password@localhost:5432/arxiv_db"
    )

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "arxiv_papers"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Groq
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"

    # Jina
    jina_api_key: str = ""
    jina_embedding_model: str = "jina-embeddings-v3"

    # Langfuse
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://localhost:3000"

    # arXiv
    arxiv_categories: str = "cs.AI,cs.LG,cs.CL"
    arxiv_max_results: int = 50

    # Telegram
    telegram_bot_token: str = ""

    # LangSmith
    langchain_tracing_v2: str = "false"
    langchain_api_key: str = ""
    langchain_project: str = "rag"
    langchain_endpoint: str = "https://api.smith.langchain.com"


settings = Settings()
