"""Transcription entity — represents the result of a transcription process."""

from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field


class TranscriptionSegment(BaseModel):
    """A time-aligned segment within a transcription.

    Attributes:
        start: Start time in seconds.
        end: End time in seconds.
        text: Transcribed text for this segment.
    """

    start: float
    end: float
    text: str

    model_config = {"frozen": True}


class Transcription(BaseModel):
    """Full transcription output for a single video.

    Attributes:
        video_path: Source video file path.
        text: Full plain-text transcription.
        segments: Time-aligned segments (can be empty for engines that don't support it).
        language: Detected or specified language code (e.g. 'pt', 'en').
        created_at: UTC timestamp of when the transcription was produced.
        model_name: Name/version of the transcription model used.
    """

    video_path: Path
    text: str
    segments: list[TranscriptionSegment] = Field(default_factory=list)
    language: str = "unknown"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_name: str = "unknown"

    model_config = {"frozen": True}

    @property
    def word_count(self) -> int:
        return len(self.text.split())

    @property
    def duration_seconds(self) -> float | None:
        """Total duration covered by segments, or None if no segments."""
        if not self.segments:
            return None
        return self.segments[-1].end - self.segments[0].start
