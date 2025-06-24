import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path

# Find and load .env file explicitly
env_path = Path('.') / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded .env file from {env_path.absolute()}")
else:
    print(f"❌ .env file not found at {env_path.absolute()}")

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://docuser:docpassword@localhost/docproc"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # JWT
    SECRET_KEY: str = "secret-key-changeme-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB

    # Environment
    ENVIRONMENT: str = "development"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 1000
    OPENAI_TEMPERATURE: float = 0.1

    WORKFLOW_ENGINE: str = "langchain" # Options: langchain, openai_direct, llamaindex, haystack

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()

# Debug output
print(f"🔍 Config loaded - DB URL: {settings.DATABASE_URL}")
print(f"🔍 Config loaded - OpenAI Key exists: {bool(settings.OPENAI_API_KEY)}")