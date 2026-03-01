"""API-layer Pydantic schemas — decoupled from domain entities."""

from datetime import datetime

from pydantic import BaseModel

from readerike.core.entities.job import JobStatus


class SegmentResponse(BaseModel):
    start: float
    end: float
    text: str


class TranscriptionResponse(BaseModel):
    text: str
    language: str
    model_name: str
    segments: list[SegmentResponse]


class JobResponse(BaseModel):
    """Full job response including optional transcription."""

    id: str
    video_filename: str
    language: str | None
    model_name: str
    status: JobStatus
    created_at: datetime
    completed_at: datetime | None
    error: str | None
    transcription: TranscriptionResponse | None

    model_config = {"from_attributes": True}


class JobListItem(BaseModel):
    """Lightweight job response — omits transcription for list endpoints."""

    id: str
    video_filename: str
    language: str | None
    model_name: str
    status: JobStatus
    created_at: datetime
    completed_at: datetime | None
    error: str | None

    model_config = {"from_attributes": True}


class JobCreateResponse(BaseModel):
    """Response immediately after creating a job."""

    id: str
    status: JobStatus
    message: str
