"""IAudioExtractor port — defines the contract for audio extraction from video."""

from abc import ABC, abstractmethod
from pathlib import Path

from readerike.core.entities.video import Video


class IAudioExtractor(ABC):
    """Extract audio from a video file.

    Implementations must not raise on valid video files and should produce
    a WAV or MP3 file at the specified output path.
    """

    @abstractmethod
    def extract(self, video: Video, output_path: Path) -> Path:
        """Extract audio from *video* and write it to *output_path*.

        Args:
            video: The source video entity.
            output_path: Desired destination for the audio file.

        Returns:
            The actual path where the audio was written (may differ from
            *output_path* if the implementation appends an extension).

        Raises:
            AudioExtractionError: If extraction fails for any reason.
        """
