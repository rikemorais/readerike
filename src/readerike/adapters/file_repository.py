"""FileTranscriptionRepository — persists transcriptions as JSON files."""

import json
import logging
from pathlib import Path

from readerike.core.entities.transcription import Transcription
from readerike.core.exceptions import RepositoryError
from readerike.core.ports.repository import ITranscriptionRepository

logger = logging.getLogger(__name__)


class FileTranscriptionRepository(ITranscriptionRepository):
    """Stores Transcription entities as human-readable JSON files.

    Each transcription is saved alongside the original video (or to a
    configurable output directory), making results easy to inspect and
    version-control when videos are small test fixtures.
    """

    def save(self, transcription: Transcription, output_path: Path) -> Path:
        """Serialize *transcription* to a JSON file at *output_path*.

        The parent directory is created automatically if it does not exist.

        Args:
            transcription: The transcription to persist.
            output_path: Target .json file path.

        Returns:
            The resolved path of the written file.

        Raises:
            RepositoryError: On any I/O failure.
        """
        output_path = output_path.with_suffix(".json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "video_path": str(transcription.video_path),
            "language": transcription.language,
            "model": transcription.model_name,
            "created_at": transcription.created_at.isoformat(),
            "word_count": transcription.word_count,
            "text": transcription.text,
            "segments": [
                {"start": seg.start, "end": seg.end, "text": seg.text}
                for seg in transcription.segments
            ],
        }

        try:
            output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as exc:
            raise RepositoryError(f"Failed to write transcription to {output_path}: {exc}") from exc

        logger.debug("Saved transcription (%d words) → %s", transcription.word_count, output_path)
        return output_path.resolve()

    def find_by_video(self, video_path: Path) -> Transcription | None:
        """Look for a previously saved transcription alongside *video_path*.

        Checks for a .json file with the same stem in the same directory.

        Returns None when no matching file is found.
        """
        candidate = video_path.with_suffix(".json")
        if not candidate.exists():
            return None

        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not load cached transcription from %s: %s", candidate, exc)
            return None

        from datetime import datetime

        from readerike.core.entities.transcription import TranscriptionSegment

        segments = [
            TranscriptionSegment(start=s["start"], end=s["end"], text=s["text"])
            for s in payload.get("segments", [])
        ]

        return Transcription(
            video_path=Path(payload["video_path"]),
            text=payload["text"],
            segments=segments,
            language=payload.get("language", "unknown"),
            model_name=payload.get("model", "unknown"),
            created_at=datetime.fromisoformat(payload["created_at"]),
        )
