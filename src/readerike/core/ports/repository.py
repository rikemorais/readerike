"""ITranscriptionRepository port — persistence contract for transcriptions."""

from abc import ABC, abstractmethod
from pathlib import Path

from readerike.core.entities.transcription import Transcription


class ITranscriptionRepository(ABC):
    """Persist and retrieve Transcription entities.

    Decouples the use case from any specific storage mechanism (filesystem,
    database, object storage, etc.).
    """

    @abstractmethod
    def save(self, transcription: Transcription, output_path: Path) -> Path:
        """Persist *transcription* and return the path/identifier used.

        Args:
            transcription: The transcription to persist.
            output_path: Suggested destination path or directory.

        Returns:
            The actual path where the transcription was stored.
        """

    @abstractmethod
    def find_by_video(self, video_path: Path) -> Transcription | None:
        """Retrieve a previously saved transcription for *video_path*.

        Returns None when no transcription exists for the given video.
        """
