from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30

    # Security & JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Application URLs
    FRONTEND_URL: str = "http://localhost:5173"
    API_BASE_URL: str = "http://localhost:8000"

    # LLM Configuration
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    GLM_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Vector Database (Qdrant)
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: Optional[str] = None

    # Embeddings
    EMBEDDING_MODEL: str = "nomic-embed-text"  # Ollama model
    EMBEDDING_DIMENSION: int = 768

    # Document Processing
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_DOCUMENT_TYPES: list = ["pdf", "docx", "txt", "md"]
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Evidence Upload (Test Results)
    EVIDENCE_UPLOAD_DIR: str = "uploads/evidence"
    MAX_EVIDENCE_SIZE_MB: int = 20  # Max size per evidence file
    ALLOWED_IMAGE_TYPES: list = ["jpg", "jpeg", "png", "gif", "webp"]
    ALLOWED_VIDEO_TYPES: list = ["mp4", "webm", "mov", "avi"]

    # Redis Cache
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    CACHE_TTL_SECONDS: int = 604800  # 7 days
    CACHE_ENABLED: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Session Persistence
    ENABLE_SESSION_PERSISTENCE: bool = True  # Re-enabled with fresh DB connection fix

    # Concurrency & Queue Management
    MAX_CONCURRENT_GENERATIONS: int = 10  # Max simultaneous generations
    ENABLE_QUEUE_MANAGEMENT: bool = True  # Enable queueing system

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
