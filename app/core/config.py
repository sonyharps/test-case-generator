from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OLLAMA_URL: str = "http://host.docker.internal:11434"

    class Config:
        env_file = ".env"

settings = Settings()
