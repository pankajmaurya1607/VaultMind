from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Enterprise Knowledge Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://eka_user:eka_pass@localhost:5432/eka_db"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://eka_user:eka_pass@localhost:5432/eka_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"

    # Groq
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-70b-versatile"

    # Local embedding
    EMBEDDING_MODEL_LOCAL: str = "BAAI/bge-small-en-v1.5"

    # PGVector
    PGVECTOR_DIMENSION: int = 1536

    # Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".md", ".csv", ".xlsx", ".txt"]

    # Chunking
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Retrieval
    TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.7

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Monitoring
    PROMETHEUS_PORT: int = 9090
    OPENTELEMETRY_ENABLED: bool = True

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
