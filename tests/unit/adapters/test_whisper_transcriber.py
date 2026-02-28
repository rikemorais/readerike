"""Unit tests for WhisperTranscriber."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from readerike.core.exceptions import TranscriptionError


@pytest.mark.unit
class TestWhisperTranscriber:
    def _make_whisper_result(self) -> dict:
        return {
            "text": " Olá mundo",
            "language": "pt",
            "segments": [
                {"start": 0.0, "end": 2.0, "text": " Olá mundo"},
            ],
        }

    def _make_transcriber(self, model_name: str = "base") -> "WhisperTranscriber":
        with patch("whisper.load_model") as mock_load:
            mock_load.return_value = MagicMock()
            from readerike.adapters.whisper_transcriber import WhisperTranscriber
            return WhisperTranscriber(model_name=model_name)

    def test_init_raises_on_invalid_model(self) -> None:
        with patch("whisper.load_model"):
            from readerike.adapters.whisper_transcriber import WhisperTranscriber
            with pytest.raises(ValueError, match="Invalid model"):
                WhisperTranscriber(model_name="invalid-model")

    def test_transcribe_returns_transcription_entity(self, tmp_wav: Path) -> None:
        transcriber = self._make_transcriber()
        transcriber._model.transcribe.return_value = self._make_whisper_result()

        from readerike.core.entities.transcription import Transcription
        result = transcriber.transcribe(tmp_wav)

        assert isinstance(result, Transcription)

    def test_transcribe_strips_text(self, tmp_wav: Path) -> None:
        transcriber = self._make_transcriber()
        transcriber._model.transcribe.return_value = self._make_whisper_result()

        result = transcriber.transcribe(tmp_wav)

        assert result.text == "Olá mundo"

    def test_transcribe_maps_segments(self, tmp_wav: Path) -> None:
        transcriber = self._make_transcriber()
        transcriber._model.transcribe.return_value = self._make_whisper_result()

        result = transcriber.transcribe(tmp_wav)

        assert len(result.segments) == 1
        assert result.segments[0].start == 0.0
        assert result.segments[0].end == 2.0

    def test_transcribe_passes_language_to_model(self, tmp_wav: Path) -> None:
        transcriber = self._make_transcriber()
        transcriber._model.transcribe.return_value = self._make_whisper_result()

        transcriber.transcribe(tmp_wav, language="pt")

        call_kwargs = transcriber._model.transcribe.call_args[1]
        assert call_kwargs.get("language") == "pt"

    def test_transcribe_does_not_pass_language_when_none(self, tmp_wav: Path) -> None:
        transcriber = self._make_transcriber()
        transcriber._model.transcribe.return_value = self._make_whisper_result()

        transcriber.transcribe(tmp_wav, language=None)

        call_kwargs = transcriber._model.transcribe.call_args[1]
        assert "language" not in call_kwargs

    def test_transcribe_raises_on_missing_audio_file(self, tmp_path: Path) -> None:
        transcriber = self._make_transcriber()
        missing = tmp_path / "nonexistent.wav"

        with pytest.raises(TranscriptionError, match="Audio file not found"):
            transcriber.transcribe(missing)

    def test_transcribe_raises_transcription_error_on_model_failure(self, tmp_wav: Path) -> None:
        transcriber = self._make_transcriber()
        transcriber._model.transcribe.side_effect = RuntimeError("CUDA OOM")

        with pytest.raises(TranscriptionError, match="Whisper transcription failed"):
            transcriber.transcribe(tmp_wav)

    def test_transcribe_handles_empty_segments(self, tmp_wav: Path) -> None:
        transcriber = self._make_transcriber()
        transcriber._model.transcribe.return_value = {
            "text": " Olá",
            "language": "pt",
            "segments": [],
        }

        result = transcriber.transcribe(tmp_wav)

        assert result.segments == []

    def test_valid_model_names_are_accepted(self) -> None:
        from readerike.adapters.whisper_transcriber import WHISPER_MODELS
        for model in WHISPER_MODELS:
            with patch("whisper.load_model"):
                from readerike.adapters.whisper_transcriber import WhisperTranscriber
                WhisperTranscriber(model_name=model)  # must not raise
