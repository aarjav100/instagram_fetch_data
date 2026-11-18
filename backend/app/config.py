import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./influencer_crm.db"

    # Anthropic
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # Instagram Graph API
    INSTAGRAM_ACCESS_TOKEN: str = ""
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str = ""  # ID of the authenticated IG business account

    # Google Sheets
    GOOGLE_SERVICE_ACCOUNT_FILE: str = "credentials.json"
    GOOGLE_SHEET_ID: str = ""
    GOOGLE_SHEET_NAME: str = "Influencer Outreach CRM"

    # Gmail API
    GMAIL_CREDENTIALS_FILE: str = "gmail_credentials.json"
    GMAIL_TOKEN_FILE: str = "token.json"
    GMAIL_USER_EMAIL: str = "me"

    # Outreach limits & delays
    DAILY_SEND_LIMIT: int = 30
    SEND_DELAY_SECONDS: int = 5
    DEFAULT_SENDER_NAME: str = "Alex - Partnerships"
    DEFAULT_BRAND_NAME: str = "Aura Bloom"

    # Schedulers
    FOLLOWUP_CHECK_INTERVAL_HOURS: int = 1
    REPLY_POLL_INTERVAL_MINUTES: int = 5

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "*"
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
