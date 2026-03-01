"""Job entity — represents a transcription job with its lifecycle state."""

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from readerike.core.entities.transcription import Transcription


class JobStatus(str, Enum):
    """Lifecycle states for a transcription job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(BaseModel):
    """Immutable representation of a transcription job.

    Attributes:
        id: UUID4 string identifier.
        video_filename: Original uploaded filename.
        video_path: Absolute path to the uploaded video file.
        language: Optional language hint passed to Whisper.
        model_name: Whisper model size (e.g. 'base', 'small').
        status: Current lifecycle state.
        created_at: UTC timestamp when the job was created.
        completed_at: UTC timestamp when the job finished (success or failure).
        error: Error message if the job failed.
        transcription: Transcription result when completed.
    """

    id: str
    video_filename: str
    video_path: Path
    language: str | None = None
    model_name: str = "base"
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    error: str | None = None
    transcription: Transcription | None = None

    model_config = {"frozen": True}
