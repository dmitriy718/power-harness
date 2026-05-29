from typing import Optional
import os

class Settings:
    def __init__(self):
        self.provider: str = os.getenv("PROVIDER", "ollama")
        self.ollama_base_url: Optional[str] = os.getenv("OLLAMA_BASE_URL")
        self.ollama_model: Optional[str] = os.getenv("OLLAMA_MODEL")
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.openai_model: Optional[str] = os.getenv("OPENAI_MODEL")
        self.database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/nova_agent.db")
        self.redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "8080"))
        self.allow_destructive: bool = os.getenv("ALLOW_DESTRUCTIVE", "false").lower() in ("1", "true", "yes")
        self.dry_run: bool = os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes")

settings = Settings()
