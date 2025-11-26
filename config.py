# backend/config.py
import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

    SECRET_KEY: str = os.getenv("JWT_SECRET", "local-dev-secret-2025")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days

    CLOUDINARY_URL: str = os.getenv("CLOUDINARY_URL", "")

    # Store origins as a RAW STRING so pydantic does NOT parse as JSON
    _ALLOWED_ORIGINS_RAW: str = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173"
    )

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        return [
            o.strip()
            for o in self._ALLOWED_ORIGINS_RAW.split(",")
            if o.strip()
        ]

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "protected_namespaces": ()
    }

settings = Settings()
