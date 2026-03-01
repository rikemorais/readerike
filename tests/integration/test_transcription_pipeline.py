"""Integration tests for the full transcription pipeline.

These tests wire real adapters together but mock FFmpeg and Whisper calls
to avoid requiring GPU/FFmpeg binaries in CI. The focus is on data flow
and contract validation between components.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from readerike.adapters.file_repository import FileTranscriptionRepository
from readerike.core.entities.transcription import Transcription, TranscriptionSegment
from readerike.core.use_cases.transcribe_video import TranscribeVideoUseCase


def _make_whisper_raw_result() -> dict:
    return {
        "text": " Olá este é um vídeo de teste",
        "language": "pt",
        "segments": [
            {"start": 0.0, "end": 3.0, "text": " Olá este é um vídeo de teste"},
        ],
    }


@pytest.mark.integration
class TestTranscriptionPipeline:
    def test_pipeline_produces_json_file(self, tmp_video: Path, tmp_path: Path) -> None:
        """End-to-end: video in → JSON file out."""
        output_dir = tmp_path / "output"

        with (
            patch("ffmpeg.input") as mock_ffmpeg,
            patch("whisper.load_model") as mock_whisper_load,
        ):
            # FFmpeg mock
            mock_stream = MagicMock()
            mock_ffmpeg.return_value = mock_stream
            mock_stream.output.return_value = mock_stream
            mock_stream.overwrite_output.return_value = mock_stream
            mock_stream.run.side_effect = lambda **_: _create_dummy_wav(tmp_path / "sample.wav")

            # Whisper mock
            mock_model = MagicMock()
            mock_whisper_load.return_value = mock_model
            mock_model.transcribe.return_value = _make_whisper_raw_result()

            from readerike.adapters.ffmpeg_extractor import FFmpegAudioExtractor
            from readerike.adapters.whisper_transcriber import WhisperTranscriber

            use_case = TranscribeVideoUseCase(
                audio_extractor=FFmpegAudioExtractor(),
                transcriber=WhisperTranscriber(model_name="base"),
                repository=FileTranscriptionRepository(),
            )
            transcription = use_case.execute(tmp_video, output_dir=output_dir)

        json_file = output_dir / "sample.json"
        assert json_file.exists(), "Expected JSON output file to be created"
        assert isinstance(transcription, Transcription)

    def test_pipeline_json_content_matches_transcription(
        self, tmp_video: Path, tmp_path: Path
    ) -> None:
        output_dir = tmp_path / "output"

        with (
            patch("ffmpeg.input") as mock_ffmpeg,
            patch("whisper.load_model") as mock_whisper_load,
        ):
            mock_stream = MagicMock()
            mock_ffmpeg.return_value = mock_stream
            mock_stream.output.return_value = mock_stream
            mock_stream.overwrite_output.return_value = mock_stream
            mock_stream.run.side_effect = lambda **_: _create_dummy_wav(tmp_path / "sample.wav")

            mock_model = MagicMock()
            mock_whisper_load.return_value = mock_model
            mock_model.transcribe.return_value = _make_whisper_raw_result()

            from readerike.adapters.ffmpeg_extractor import FFmpegAudioExtractor
            from readerike.adapters.whisper_transcriber import WhisperTranscriber

            use_case = TranscribeVideoUseCase(
                audio_extractor=FFmpegAudioExtractor(),
                transcriber=WhisperTranscriber(model_name="base"),
                repository=FileTranscriptionRepository(),
            )
            transcription = use_case.execute(tmp_video, output_dir=output_dir, language="pt")

        json_file = output_dir / "sample.json"
        payload = json.loads(json_file.read_text(encoding="utf-8"))

        assert payload["text"] == transcription.text
        assert payload["language"] == "pt"
        assert payload["model"] == "base"
        assert len(payload["segments"]) == 1

    def test_pipeline_find_by_video_returns_saved_transcription(
        self, tmp_video: Path, tmp_path: Path
    ) -> None:
        """Saved transcription can be retrieved from disk via repository."""
        output_dir = tmp_path / "output"
        repo = FileTranscriptionRepository()

        with (
            patch("ffmpeg.input") as mock_ffmpeg,
            patch("whisper.load_model") as mock_whisper_load,
        ):
            mock_stream = MagicMock()
            mock_ffmpeg.return_value = mock_stream
            mock_stream.output.return_value = mock_stream
            mock_stream.overwrite_output.return_value = mock_stream
            mock_stream.run.side_effect = lambda **_: _create_dummy_wav(tmp_path / "sample.wav")

            mock_model = MagicMock()
            mock_whisper_load.return_value = mock_model
            mock_model.transcribe.return_value = _make_whisper_raw_result()

            from readerike.adapters.ffmpeg_extractor import FFmpegAudioExtractor
            from readerike.adapters.whisper_transcriber import WhisperTranscriber

            use_case = TranscribeVideoUseCase(
                audio_extractor=FFmpegAudioExtractor(),
                transcriber=WhisperTranscriber(model_name="base"),
                repository=repo,
            )
            use_case.execute(tmp_video, output_dir=output_dir)

        # Find by json path with matching stem
        saved_json = output_dir / "sample.json"
        retrieved = repo.find_by_video(saved_json.with_suffix(".mp4"))
        # find_by_video looks next to the video path, so test via the json directly
        retrieved = repo.find_by_video(saved_json.with_suffix(".mp4"))

        # The json is in output_dir, not next to tmp_video, so result is None
        # (correct behaviour: find_by_video looks alongside the video file)
        assert retrieved is None  # video is in tmp_path, json is in output_dir

        # Manually read the saved JSON to verify round-trip integrity
        loaded = repo.find_by_video(saved_json.with_suffix(".mp4").parent / "sample.mp4")
        # Still None because video is not in output_dir — this is expected.
        # Verify by placing the json next to a fake video and loading it:
        fake_video = output_dir / "sample.mp4"
        fake_video.write_bytes(b"\x00" * 64)
        loaded = repo.find_by_video(fake_video)

        assert loaded is not None
        assert loaded.text == "Olá este é um vídeo de teste"


def _create_dummy_wav(path: Path) -> None:
    """Helper used by run() side_effect to create a dummy WAV so the path exists."""
    import wave
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16_000)
        wf.writeframes(b"\x00" * 32_000)
