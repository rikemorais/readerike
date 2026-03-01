"""FastAPI dependency providers."""

from functools import lru_cache

from readerike.adapters.ffmpeg_extractor import FFmpegAudioExtractor
from readerike.adapters.file_repository import FileTranscriptionRepository
from readerike.adapters.sqlite_job_repository import SQLiteJobRepository
from readerike.adapters.whisper_transcriber import WhisperTranscriber
from readerike.core.use_cases.transcribe_video import TranscribeVideoUseCase
from readerike.infrastructure.config import Settings


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_job_repository() -> SQLiteJobRepository:
    """Return the singleton SQLiteJobRepository.

    The repository is initialised during the app lifespan, so by the time
    a request arrives the database table already exists.
    """
    settings = get_settings()
    return SQLiteJobRepository(db_path=settings.db_path)


@lru_cache
def get_use_case() -> TranscribeVideoUseCase:
    settings = get_settings()
    return TranscribeVideoUseCase(
        audio_extractor=FFmpegAudioExtractor(),
        transcriber=WhisperTranscriber(
            model_name=settings.whisper_model,
            device=settings.whisper_device,
        ),
        repository=FileTranscriptionRepository(),
    )
