"""Unit tests for FFmpegAudioExtractor."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from readerike.adapters.ffmpeg_extractor import FFmpegAudioExtractor
from readerike.core.entities.video import Video
from readerike.core.exceptions import AudioExtractionError


@pytest.mark.unit
class TestFFmpegAudioExtractor:
    def test_extract_returns_wav_path(self, tmp_video: Path, tmp_path: Path) -> None:
        extractor = FFmpegAudioExtractor()
        video = Video(path=tmp_video)
        output = tmp_path / "audio.wav"

        with patch("ffmpeg.input") as mock_input:
            mock_stream = MagicMock()
            mock_input.return_value = mock_stream
            mock_stream.output.return_value = mock_stream
            mock_stream.overwrite_output.return_value = mock_stream
            mock_stream.run.return_value = None

            result = extractor.extract(video, output)

        assert result.suffix == ".wav"

    def test_extract_forces_wav_extension(self, tmp_video: Path, tmp_path: Path) -> None:
        extractor = FFmpegAudioExtractor()
        video = Video(path=tmp_video)
        output = tmp_path / "audio.mp3"  # wrong extension

        with patch("ffmpeg.input") as mock_input:
            mock_stream = MagicMock()
            mock_input.return_value = mock_stream
            mock_stream.output.return_value = mock_stream
            mock_stream.overwrite_output.return_value = mock_stream
            mock_stream.run.return_value = None

            result = extractor.extract(video, output)

        assert result.suffix == ".wav"

    def test_extract_calls_ffmpeg_with_correct_args(self, tmp_video: Path, tmp_path: Path) -> None:
        extractor = FFmpegAudioExtractor()
        video = Video(path=tmp_video)
        output = tmp_path / "audio.wav"

        with patch("ffmpeg.input") as mock_input:
            mock_stream = MagicMock()
            mock_input.return_value = mock_stream
            mock_stream.output.return_value = mock_stream
            mock_stream.overwrite_output.return_value = mock_stream
            mock_stream.run.return_value = None

            extractor.extract(video, output)

        mock_input.assert_called_once_with(str(tmp_video))
        call_kwargs = mock_stream.output.call_args[1]
        assert call_kwargs["ar"] == 16_000
        assert call_kwargs["ac"] == 1
        assert call_kwargs["acodec"] == "pcm_s16le"

    def test_extract_raises_audio_extraction_error_on_ffmpeg_failure(
        self, tmp_video: Path, tmp_path: Path
    ) -> None:
        import ffmpeg as ffmpeg_lib

        extractor = FFmpegAudioExtractor()
        video = Video(path=tmp_video)
        output = tmp_path / "audio.wav"

        with patch("ffmpeg.input") as mock_input:
            mock_stream = MagicMock()
            mock_input.return_value = mock_stream
            mock_stream.output.return_value = mock_stream
            mock_stream.overwrite_output.return_value = mock_stream
            mock_stream.run.side_effect = ffmpeg_lib.Error("ffmpeg", None, b"no audio stream")

            with pytest.raises(AudioExtractionError, match="FFmpeg failed"):
                extractor.extract(video, output)

    def test_extract_creates_parent_directory(self, tmp_video: Path, tmp_path: Path) -> None:
        extractor = FFmpegAudioExtractor()
        video = Video(path=tmp_video)
        nested_output = tmp_path / "nested" / "dir" / "audio.wav"

        with patch("ffmpeg.input") as mock_input:
            mock_stream = MagicMock()
            mock_input.return_value = mock_stream
            mock_stream.output.return_value = mock_stream
            mock_stream.overwrite_output.return_value = mock_stream
            mock_stream.run.return_value = None

            extractor.extract(video, nested_output)

        assert nested_output.parent.exists()
