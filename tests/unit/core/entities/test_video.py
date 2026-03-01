"""Unit tests for the Video entity."""

import pytest
from pydantic import ValidationError

from readerike.core.entities.video import Video


@pytest.mark.unit
class TestVideo:
    def test_create_video_with_valid_path(self, tmp_video):
        video = Video(path=tmp_video)
        assert video.path == tmp_video.resolve()

    def test_format_derived_from_extension(self, tmp_video):
        video = Video(path=tmp_video)
        assert video.format == "mp4"

    def test_explicit_format_overrides_extension(self, tmp_video):
        video = Video(path=tmp_video, format="mov")
        assert video.format == "mov"

    def test_stem_returns_filename_without_extension(self, tmp_video):
        video = Video(path=tmp_video)
        assert video.stem == "sample"

    def test_str_returns_path_string(self, tmp_video):
        video = Video(path=tmp_video)
        assert str(video) == str(tmp_video.resolve())

    def test_video_is_immutable(self, tmp_video):
        video = Video(path=tmp_video)
        with pytest.raises(ValidationError):
            video.format = "avi"  # type: ignore[misc]

    def test_nonexistent_path_raises(self, tmp_path):
        with pytest.raises(ValueError, match="not found"):
            Video(path=tmp_path / "ghost.mp4")

    def test_duration_defaults_to_none(self, tmp_video):
        video = Video(path=tmp_video)
        assert video.duration_seconds is None
