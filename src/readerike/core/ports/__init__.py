"""Ports — abstract interfaces that decouple the core from infrastructure."""

from readerike.core.ports.audio_extractor import IAudioExtractor
from readerike.core.ports.job_repository import IJobRepository
from readerike.core.ports.repository import ITranscriptionRepository
from readerike.core.ports.transcriber import ITranscriber

__all__ = ["IAudioExtractor", "ITranscriber", "ITranscriptionRepository", "IJobRepository"]
