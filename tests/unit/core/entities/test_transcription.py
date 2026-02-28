"""Unit tests for the Transcription and TranscriptionSegment entities."""

from pathlib import Path

import pytest

from readerike.core.entities.transcription import Transcription, TranscriptionSegment


@pytest.mark.unit
class TestTranscriptionSegment:
    def test_create_segment(self):
        seg = TranscriptionSegment(start=0.0, end=2.5, text="Olá mundo")
        assert seg.start == 0.0
        assert seg.end == 2.5
        assert seg.text == "Olá mundo"

    def test_segment_is_immutable(self):
        seg = TranscriptionSegment(start=0.0, end=1.0, text="test")
        with pytest.raises(Exception):
            seg.text = "changed"  # type: ignore[misc]


@pytest.mark.unit
class TestTranscription:
    def test_word_count_counts_space_separated_words(self):
        t = Transcription(video_path=Path("/tmp/v.mp4"), text="um dois três quatro cinco")
        assert t.word_count == 5

    def test_word_count_empty_text(self):
        t = Transcription(video_path=Path("/tmp/v.mp4"), text="")
        assert t.word_count == 1  # "".split() → [""], len = 1; edge case

    def test_duration_returns_none_with_no_segments(self):
        t = Transcription(video_path=Path("/tmp/v.mp4"), text="hello")
        assert t.duration_seconds is None

    def test_duration_computed_from_segments(self):
        segments = [
            TranscriptionSegment(start=1.0, end=3.0, text="a"),
            TranscriptionSegment(start=3.0, end=7.0, text="b"),
        ]
        t = Transcription(video_path=Path("/tmp/v.mp4"), text="a b", segments=segments)
        assert t.duration_seconds == pytest.approx(6.0)

    def test_language_defaults_to_unknown(self):
        t = Transcription(video_path=Path("/tmp/v.mp4"), text="x")
        assert t.language == "unknown"

    def test_created_at_is_set_automatically(self):
        t = Transcription(video_path=Path("/tmp/v.mp4"), text="x")
        assert t.created_at is not None
