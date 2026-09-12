"""Application settings loaded from environment / .env."""

from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "AI Assistant Platform"
    APP_ENV: str = "dev"
    APP_SECRET: str = "change-me-in-local-dev"
    DEBUG: bool = True

    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str = "ai_assistant"
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""

    QDRANT_URL: str = "http://127.0.0.1:6333"
    QDRANT_API_KEY: str = ""

    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"

    EMBEDDING_BASE_URL: str = "https://api.openai.com/v1"
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536
    EMBEDDING_PROVIDER: str = "fake"  # fake | openai_compatible

    QDRANT_COLLECTION: str = "knowledge_chunks"

    LLM_PROVIDER: str = "fake"  # fake | openai_compatible
    RAG_TOP_K: int = 5
    RAG_SCORE_THRESHOLD: float | None = None
    RAG_REFUSE_MESSAGE: str = "当前知识库中未找到可靠依据。"

    FILE_STORAGE_PATH: str = "./data/files"
    MAX_UPLOAD_SIZE_MB: int = 20

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5666",
            "http://127.0.0.1:5666",
        ]
    )

    @property
    def database_url(self) -> str:
        # Encode so passwords with @ : / etc. stay valid in the URL
        user = quote_plus(self.MYSQL_USER)
        password = quote_plus(self.MYSQL_PASSWORD)
        return (
            f"mysql+aiomysql://{user}:{password}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            "?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
