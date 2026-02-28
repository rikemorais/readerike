"""Adapters — concrete implementations of the core ports."""

from readerike.adapters.ffmpeg_extractor import FFmpegAudioExtractor
from readerike.adapters.file_repository import FileTranscriptionRepository
from readerike.adapters.whisper_transcriber import WhisperTranscriber

__all__ = ["FFmpegAudioExtractor", "WhisperTranscriber", "FileTranscriptionRepository"]
