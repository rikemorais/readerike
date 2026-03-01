"""Unit tests for FileTranscriptionRepository."""

import json
from pathlib import Path

import pytest

from readerike.adapters.file_repository import FileTranscriptionRepository
from readerike.core.entities.transcription import Transcription, TranscriptionSegment
from readerike.core.exceptions import RepositoryError


def _make_transcription(video_path: Path) -> Transcription:
    return Transcription(
        video_path=video_path,
        text="Olá mundo este é um teste",
        segments=[
            TranscriptionSegment(start=0.0, end=2.5, text="Olá mundo este é um"),
            TranscriptionSegment(start=2.5, end=4.0, text="teste"),
        ],
        language="pt",
        model_name="base",
    )


@pytest.mark.unit
class TestFileTranscriptionRepository:
    def test_save_creates_json_file(self, tmp_path: Path) -> None:
        repo = FileTranscriptionRepository()
        transcription = _make_transcription(tmp_path / "video.mp4")
        output_path = tmp_path / "output.json"

        result = repo.save(transcription, output_path)

        assert result.exists()
        assert result.suffix == ".json"

    def test_save_json_has_correct_keys(self, tmp_path: Path) -> None:
        repo = FileTranscriptionRepository()
        transcription = _make_transcription(tmp_path / "video.mp4")

        saved = repo.save(transcription, tmp_path / "out.json")
        payload = json.loads(saved.read_text(encoding="utf-8"))

        expected_keys = {
            "video_path",
            "language",
            "model",
            "created_at",
            "word_count",
            "text",
            "segments",
        }
        assert expected_keys == set(payload.keys())

    def test_save_text_matches_transcription(self, tmp_path: Path) -> None:
        repo = FileTranscriptionRepository()
        transcription = _make_transcription(tmp_path / "video.mp4")

        saved = repo.save(transcription, tmp_path / "out.json")
        payload = json.loads(saved.read_text(encoding="utf-8"))

        assert payload["text"] == transcription.text

    def test_save_segments_are_serialized(self, tmp_path: Path) -> None:
        repo = FileTranscriptionRepository()
        transcription = _make_transcription(tmp_path / "video.mp4")

        saved = repo.save(transcription, tmp_path / "out.json")
        payload = json.loads(saved.read_text(encoding="utf-8"))

        assert len(payload["segments"]) == 2
        assert payload["segments"][0] == {"start": 0.0, "end": 2.5, "text": "Olá mundo este é um"}

    def test_save_forces_json_extension(self, tmp_path: Path) -> None:
        repo = FileTranscriptionRepository()
        transcription = _make_transcription(tmp_path / "video.mp4")

        saved = repo.save(transcription, tmp_path / "out.txt")

        assert saved.suffix == ".json"

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        repo = FileTranscriptionRepository()
        transcription = _make_transcription(tmp_path / "video.mp4")
        nested = tmp_path / "a" / "b" / "c" / "out.json"

        saved = repo.save(transcription, nested)

        assert saved.exists()

    def test_find_by_video_returns_none_when_missing(self, tmp_path: Path) -> None:
        repo = FileTranscriptionRepository()

        result = repo.find_by_video(tmp_path / "nonexistent.mp4")

        assert result is None

    def test_find_by_video_loads_saved_transcription(
        self, tmp_path: Path, sample_transcription_json: Path
    ) -> None:
        repo = FileTranscriptionRepository()
        video_path = sample_transcription_json.with_suffix(".mp4")

        result = repo.find_by_video(video_path)

        assert result is not None
        assert result.text == "Olá mundo este é um teste"
        assert result.language == "pt"
        assert len(result.segments) == 2

    def test_find_by_video_returns_none_on_corrupt_json(self, tmp_path: Path) -> None:
        repo = FileTranscriptionRepository()
        corrupt = tmp_path / "video.json"
        corrupt.write_text("not-json", encoding="utf-8")

        result = repo.find_by_video(tmp_path / "video.mp4")

        assert result is None

    def test_save_raises_repository_error_on_io_failure(self, tmp_path: Path) -> None:
        from unittest.mock import patch

        repo = FileTranscriptionRepository()
        transcription = _make_transcription(tmp_path / "video.mp4")

        with patch("pathlib.Path.write_text", side_effect=OSError("disk full")):
            with pytest.raises(RepositoryError, match="disk full"):
                repo.save(transcription, tmp_path / "out.json")
