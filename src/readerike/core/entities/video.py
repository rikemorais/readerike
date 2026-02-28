"""Video entity — represents an input video file in the domain."""

from pathlib import Path

from pydantic import BaseModel, field_validator


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

    @field_validator("path")
    @classmethod
    def path_must_exist(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"Video file not found: {v}")
        return v.resolve()

    @field_validator("format", mode="before")
    @classmethod
    def derive_format(cls, v: str, info: object) -> str:  # type: ignore[override]
        """Derive format from file extension when not explicitly provided."""
        if v:
            return v.lower().lstrip(".")
        # Access path from the already-validated fields via info
        data = getattr(info, "data", {})
        path = data.get("path")
        if path:
            return Path(path).suffix.lower().lstrip(".")
        return v

    @property
    def stem(self) -> str:
        """File name without extension."""
        return self.path.stem

    def __str__(self) -> str:
        return str(self.path)
