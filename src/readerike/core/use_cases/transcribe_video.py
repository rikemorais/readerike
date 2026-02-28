"""TranscribeVideoUseCase — orchestrates the full video transcription pipeline."""

import logging
import tempfile
from pathlib import Path

from readerike.core.entities.transcription import Transcription
from readerike.core.entities.video import Video
from readerike.core.ports.audio_extractor import IAudioExtractor
from readerike.core.ports.repository import ITranscriptionRepository
from readerike.core.ports.transcriber import ITranscriber

logger = logging.getLogger(__name__)


class TranscribeVideoUseCase:
    """Orchestrate extraction → transcription → persistence.

    Follows the Single Responsibility and Dependency Inversion principles:
    each step is delegated to an injected port, making the use case
    independent of concrete technologies (FFmpeg, Whisper, filesystem, etc.).
    """

    def __init__(
        self,
        audio_extractor: IAudioExtractor,
        transcriber: ITranscriber,
        repository: ITranscriptionRepository,
    ) -> None:
        self._audio_extractor = audio_extractor
        self._transcriber = transcriber
        self._repository = repository

    def execute(
        self,
        video_path: Path,
        output_dir: Path,
        language: str | None = None,
    ) -> Transcription:
        """Transcribe a video file end-to-end.

        Pipeline:
            1. Validate & create the Video entity.
            2. Extract audio to a temporary file.
            3. Transcribe the audio.
            4. Persist the result and return it.

        Args:
            video_path: Path to the input video.
            output_dir: Directory where the transcription file will be saved.
            language: Optional language hint passed to the transcription engine.

        Returns:
            A fully populated Transcription entity.
        """
        logger.info("Starting transcription pipeline for: %s", video_path)

        video = Video(path=video_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as tmp_dir:
            audio_path = Path(tmp_dir) / f"{video.stem}.wav"

            logger.debug("Extracting audio to: %s", audio_path)
            audio_path = self._audio_extractor.extract(video, audio_path)

            logger.debug("Transcribing audio with language=%s", language or "auto")
            transcription = self._transcriber.transcribe(audio_path, language)

        output_path = output_dir / f"{video.stem}.json"
        saved_path = self._repository.save(transcription, output_path)
        logger.info("Transcription saved to: %s", saved_path)

        return transcription
