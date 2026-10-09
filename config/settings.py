from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    discord_token: str = os.getenv("DISCORD_TOKEN", "")
    discord_client_id: str = os.getenv("DISCORD_CLIENT_ID", "")
    discord_guild_id: str | None = os.getenv("DISCORD_GUILD_ID") or None
    admin_ids: set[int] = frozenset(int(item.strip()) for item in os.getenv("ADMIN_IDS", "").split(",") if item.strip())

    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    ai_primary_provider: str = os.getenv("AI_PRIMARY_PROVIDER", "openrouter")
    ai_fallback_order: list[str] = tuple(part.strip() for part in os.getenv("AI_FALLBACK_ORDER", "groq,gemini").split(",") if part.strip())

    search_provider: str = os.getenv("SEARCH_PROVIDER", "tavily")
    search_api_key: str = os.getenv("SEARCH_API_KEY", "")

    database_path: Path = Path(os.getenv("DATABASE_PATH", "storage/ai_agent.db")).resolve()
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
    max_video_duration: int = int(os.getenv("MAX_VIDEO_DURATION", "60"))
    max_concurrent_jobs: int = int(os.getenv("MAX_CONCURRENT_JOBS", "2"))
    temp_file_retention_minutes: int = int(os.getenv("TEMP_FILE_RETENTION_MINUTES", "30"))

    vps_monitoring_enabled: bool = os.getenv("VPS_MONITORING_ENABLED", "true").lower() == "true"
    vps_monitor_interval_seconds: int = int(os.getenv("VPS_MONITOR_INTERVAL_SECONDS", "60"))
    vps_alert_cooldown_seconds: int = int(os.getenv("VPS_ALERT_COOLDOWN_SECONDS", "300"))
    vps_ssh_connect_timeout: int = int(os.getenv("VPS_SSH_CONNECT_TIMEOUT", "10"))

    video_ai_provider: str = os.getenv("VIDEO_AI_PROVIDER", "")
    video_ai_api_key: str = os.getenv("VIDEO_AI_API_KEY", "")

    @property
    def storage_root(self) -> Path:
        return self.database_path.parent


def ensure_storage_dirs() -> None:
    root = Path(__file__).resolve().parents[1]
    for path in [
        root / "storage" / "temp",
        root / "storage" / "output",
        root / "storage",
    ]:
        path.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    ensure_storage_dirs()
    return Settings()
