"""Application configuration loaded from environment variables or defaults."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration using pydantic-settings for env-var support.

    All fields can be overridden via environment variables with the
    READERIKE_ prefix (e.g. READERIKE_WHISPER_MODEL=large).
    """

    # Whisper
    whisper_model: str = Field(default="base", description="Whisper model size")
    whisper_device: str = Field(default="cpu", description="Torch device (cpu/cuda)")

    # Output
    output_dir: Path = Field(default=Path("outputs"), description="Default output directory")

    # API
    upload_dir: Path = Field(default=Path("uploads"), description="Directory for uploaded videos")
    db_path: Path = Field(default=Path("data/readerike.db"), description="SQLite database path")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins (JSON array via env var)",
    )

    # Logging
    log_level: str = Field(default="INFO", description="Python log level name")

    model_config = {"env_prefix": "READERIKE_", "env_file": ".env", "extra": "ignore"}


# Module-level singleton — import this instead of instantiating per call
settings = Settings()
