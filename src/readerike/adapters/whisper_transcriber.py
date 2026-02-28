"""WhisperTranscriber — transcribes audio using OpenAI Whisper (local)."""

import logging
from pathlib import Path
from typing import Any

from readerike.core.entities.transcription import Transcription, TranscriptionSegment
from readerike.core.exceptions import TranscriptionError
from readerike.core.ports.transcriber import ITranscriber

logger = logging.getLogger(__name__)

# Supported Whisper model sizes in ascending order of accuracy/cost
WHISPER_MODELS = ("tiny", "base", "small", "medium", "large", "large-v2", "large-v3")


class WhisperTranscriber(ITranscriber):
    """Wraps OpenAI Whisper for local speech-to-text transcription.

    The model is loaded once at construction time and reused across calls,
    avoiding the overhead of reloading weights for batch processing.
    """

    def __init__(self, model_name: str = "base", device: str = "cpu") -> None:
        """Load the Whisper model into memory.

        Args:
            model_name: Whisper model size. See WHISPER_MODELS for valid values.
                        Defaults to 'base' which balances speed and accuracy.
            device: Torch device ('cpu' or 'cuda'). Use 'cuda' for GPU acceleration.
        """
        if model_name not in WHISPER_MODELS:
            raise ValueError(f"Invalid model '{model_name}'. Choose from: {WHISPER_MODELS}")

        logger.info("Loading Whisper model '%s' on device '%s'", model_name, device)

        try:
            import whisper  # imported lazily to avoid mandatory dependency at import time

            self._model = whisper.load_model(model_name, device=device)
            self._model_name = model_name
        except ImportError as exc:
            raise ImportError(
                "openai-whisper is not installed. Run: pip install openai-whisper"
            ) from exc

    def transcribe(self, audio_path: Path, language: str | None = None) -> Transcription:
        """Transcribe *audio_path* using the loaded Whisper model.

        Args:
            audio_path: Path to the audio file (WAV recommended).
            language: BCP-47 language hint. None triggers Whisper's auto-detect.

        Returns:
            A populated Transcription entity with segments when available.

        Raises:
            TranscriptionError: On any Whisper failure.
        """
        if not audio_path.exists():
            raise TranscriptionError(f"Audio file not found: {audio_path}")

        logger.debug("Whisper transcribing: %s (lang=%s)", audio_path, language or "auto")

        try:
            options: dict[str, Any] = {"fp16": False}
            if language:
                options["language"] = language

            result: dict[str, Any] = self._model.transcribe(str(audio_path), **options)
        except Exception as exc:
            raise TranscriptionError(f"Whisper transcription failed: {exc}") from exc

        segments = [
            TranscriptionSegment(
                start=seg["start"],
                end=seg["end"],
                text=seg["text"].strip(),
            )
            for seg in result.get("segments", [])
        ]

        return Transcription(
            video_path=audio_path,  # use audio_path as identifier; overridden by use case
            text=result["text"].strip(),
            segments=segments,
            language=result.get("language", language or "unknown"),
            model_name=self._model_name,
        )
