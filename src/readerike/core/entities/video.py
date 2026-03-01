"""Video entity — represents an input video file in the domain."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, field_validator, model_validator


class Video(BaseModel):
    """Immutable representation of a video file.

    Attributes:
        path: Absolute path to the video file.
        format: File extension without dot (e.g. 'mp4', 'mov').
        duration_seconds: Optional pre-computed duration in seconds.
    """

    path: Path
    format: str = ""
    duration_seconds: float | None = None

    model_config = {"frozen": True}

    @model_validator(mode="before")
    @classmethod
    def derive_format_from_path(cls, data: Any) -> Any:
        """Derive format from file extension when not explicitly provided."""
        if isinstance(data, dict) and not data.get("format"):
            path = data.get("path")
            if path:
                data["format"] = Path(str(path)).suffix.lower().lstrip(".")
        return data

    @field_validator("path")
    @classmethod
    def path_must_exist(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"Video file not found: {v}")
        return v.resolve()

    @property
    def stem(self) -> str:
        """File name without extension."""
        return self.path.stem

    def __str__(self) -> str:
        return str(self.path)
