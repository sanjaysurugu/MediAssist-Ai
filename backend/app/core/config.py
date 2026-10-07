import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "MediAssist AI Platform"
    API_V1_STR: str = "/api/v1"
    
    # Environment mode
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database Configuration
    # Default to PostgreSQL connection string; can fallback to SQLite if needed for quick testing
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "mediassist_db"
    
    # Database URL constructed dynamically or overridden via env
    DATABASE_URL: str = ""

    # Default administrator account for initial local database seeding.
    ADMIN_EMAIL: str = "sanjay12@gmail.com"
    ADMIN_PASSWORD: str = ""

    # SMTP settings for password reset emails. Use a Gmail App Password, not the account password.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_USE_SSL: bool = False
    SMTP_USE_STARTTLS: bool = True
    SMTP_TIMEOUT_SECONDS: int = 10
    FEEDBACK_RECIPIENT_EMAIL: str = "sanjays60641@gmail.com"
    FRONTEND_BASE_URL: str = "http://localhost:5175"
    PASSWORD_RESET_TOKEN_MINUTES: int = 30

    # Security & JWT Token Configuration
    # IMPORTANT: In production, generate a strong 256-bit random key: openssl rand -hex 32
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day expiration
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7          # 7 days expiration

    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def frontend_url(self) -> str:
        url = self.FRONTEND_BASE_URL.strip().rstrip("/")
        if url and "://" not in url:
            return f"https://{url}"
        return url


# Instantiated global settings object
settings = Settings()
