"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Immutable application settings sourced from .env / environment."""

    google_api_key: str = field(
        default_factory=lambda: os.environ.get("GOOGLE_API_KEY", "")
    )
    telegram_bot_token: str = field(
        default_factory=lambda: os.environ.get("TELEGRAM_BOT_TOKEN", "")
    )
    telegram_chat_id: str = field(
        default_factory=lambda: os.environ.get("TELEGRAM_CHAT_ID", "")
    )
    search_query: str = field(
        default_factory=lambda: os.environ.get("SEARCH_QUERY", "香港機票快閃優惠")
    )
    max_crawl_depth: int = field(
        default_factory=lambda: int(os.environ.get("MAX_CRAWL_DEPTH", "4"))
    )
    max_concurrent_scrapes: int = field(
        default_factory=lambda: int(os.environ.get("MAX_CONCURRENT_SCRAPES", "3"))
    )
    model_name: str = "gemini-2.5-flash"


settings = Settings()
