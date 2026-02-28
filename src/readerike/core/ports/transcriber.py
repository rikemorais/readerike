"""ITranscriber port — defines the contract for speech-to-text engines."""

from abc import ABC, abstractmethod
from pathlib import Path

from readerike.core.entities.transcription import Transcription


class ITranscriber(ABC):
    """Convert an audio file into a Transcription entity.

    This is the primary extension point: swap Whisper for AssemblyAI,
    Deepgram, or any other engine by providing a new ITranscriber adapter.
    """

    @abstractmethod
    def transcribe(self, audio_path: Path, language: str | None = None) -> Transcription:
        """Transcribe the audio file at *audio_path*.

        Args:
            audio_path: Path to the audio file (WAV, MP3, FLAC, etc.).
            language: BCP-47 language hint (e.g. 'pt', 'en'). Pass None for
                      auto-detection when the engine supports it.

        Returns:
            A populated Transcription entity.

        Raises:
            TranscriptionError: If the transcription engine fails.
        """
