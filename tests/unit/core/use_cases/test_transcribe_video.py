"""Unit tests for TranscribeVideoUseCase."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from readerike.core.entities.transcription import Transcription, TranscriptionSegment
from readerike.core.entities.video import Video
from readerike.core.use_cases.transcribe_video import TranscribeVideoUseCase


def _make_transcription(video_path: Path) -> Transcription:
    return Transcription(
        video_path=video_path,
        text="Olá mundo",
        segments=[TranscriptionSegment(start=0.0, end=2.0, text="Olá mundo")],
        language="pt",
        model_name="base",
    )


@pytest.mark.unit
class TestTranscribeVideoUseCase:
    def _make_use_case(
        self, tmp_video: Path
    ) -> tuple[TranscribeVideoUseCase, MagicMock, MagicMock, MagicMock]:
        extractor = MagicMock()
        transcriber = MagicMock()
        repository = MagicMock()

        audio_path = tmp_video.parent / "audio.wav"
        extractor.extract.return_value = audio_path
        transcriber.transcribe.return_value = _make_transcription(tmp_video)
        repository.save.return_value = tmp_video.parent / "sample.json"

        use_case = TranscribeVideoUseCase(
            audio_extractor=extractor,
            transcriber=transcriber,
            repository=repository,
        )
        return use_case, extractor, transcriber, repository

    def test_execute_calls_pipeline_in_order(self, tmp_video: Path, tmp_path: Path) -> None:
        use_case, extractor, transcriber, repository = self._make_use_case(tmp_video)

        result = use_case.execute(tmp_video, output_dir=tmp_path)

        assert extractor.extract.call_count == 1
        assert transcriber.transcribe.call_count == 1
        assert repository.save.call_count == 1
        assert isinstance(result, Transcription)

    def test_execute_passes_video_entity_to_extractor(
        self, tmp_video: Path, tmp_path: Path
    ) -> None:
        use_case, extractor, transcriber, repository = self._make_use_case(tmp_video)

        use_case.execute(tmp_video, output_dir=tmp_path)

        video_arg = extractor.extract.call_args[0][0]
        assert isinstance(video_arg, Video)
        assert video_arg.path == tmp_video

    def test_execute_passes_language_to_transcriber(self, tmp_video: Path, tmp_path: Path) -> None:
        use_case, extractor, transcriber, repository = self._make_use_case(tmp_video)

        use_case.execute(tmp_video, output_dir=tmp_path, language="pt")

        _, lang_arg = transcriber.transcribe.call_args[0]
        assert lang_arg == "pt"

    def test_execute_passes_none_language_by_default(self, tmp_video: Path, tmp_path: Path) -> None:
        use_case, extractor, transcriber, repository = self._make_use_case(tmp_video)

        use_case.execute(tmp_video, output_dir=tmp_path)

        _, lang_arg = transcriber.transcribe.call_args[0]
        assert lang_arg is None

    def test_execute_creates_output_dir_if_missing(self, tmp_video: Path, tmp_path: Path) -> None:
        use_case, _, _, _ = self._make_use_case(tmp_video)
        new_dir = tmp_path / "nested" / "output"

        use_case.execute(tmp_video, output_dir=new_dir)

        assert new_dir.exists()

    def test_execute_saves_with_correct_json_filename(
        self, tmp_video: Path, tmp_path: Path
    ) -> None:
        use_case, _, _, repository = self._make_use_case(tmp_video)

        use_case.execute(tmp_video, output_dir=tmp_path)

        save_args = repository.save.call_args[0]
        saved_path: Path = save_args[1]
        assert saved_path.name == "sample.json"
        assert saved_path.parent == tmp_path

    def test_execute_returns_transcription_from_transcriber(
        self, tmp_video: Path, tmp_path: Path
    ) -> None:
        use_case, _, transcriber, _ = self._make_use_case(tmp_video)
        expected = _make_transcription(tmp_video)
        transcriber.transcribe.return_value = expected

        result = use_case.execute(tmp_video, output_dir=tmp_path)

        assert result is expected

    def test_execute_propagates_extractor_error(self, tmp_video: Path, tmp_path: Path) -> None:
        from readerike.core.exceptions import AudioExtractionError

        use_case, extractor, _, _ = self._make_use_case(tmp_video)
        extractor.extract.side_effect = AudioExtractionError("ffmpeg failed")

        with pytest.raises(AudioExtractionError, match="ffmpeg failed"):
            use_case.execute(tmp_video, output_dir=tmp_path)

    def test_execute_propagates_transcriber_error(self, tmp_video: Path, tmp_path: Path) -> None:
        from readerike.core.exceptions import TranscriptionError

        use_case, _, transcriber, _ = self._make_use_case(tmp_video)
        transcriber.transcribe.side_effect = TranscriptionError("whisper failed")

        with pytest.raises(TranscriptionError, match="whisper failed"):
            use_case.execute(tmp_video, output_dir=tmp_path)
