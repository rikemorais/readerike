"""Shared pytest fixtures available across all test modules."""

import json
import wave
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_video(tmp_path: Path) -> Path:
    """Create a minimal placeholder video file (not a real video, for path tests only)."""
    video = tmp_path / "sample.mp4"
    video.write_bytes(b"\x00" * 1024)  # placeholder binary content
    return video


@pytest.fixture()
def tmp_wav(tmp_path: Path) -> Path:
    """Create a minimal valid 16 kHz mono WAV file (1 second of silence)."""
    wav_path = tmp_path / "audio.wav"
    sample_rate = 16_000
    num_samples = sample_rate  # 1 second

    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00" * num_samples * 2)

    return wav_path


@pytest.fixture()
def sample_transcription_json(tmp_path: Path) -> Path:
    """Write a sample transcription JSON file and return its path."""
    payload = {
        "video_path": "/tmp/video.mp4",
        "language": "pt",
        "model": "base",
        "created_at": "2024-01-01T00:00:00+00:00",
        "word_count": 5,
        "text": "Olá mundo este é um teste",
        "segments": [
            {"start": 0.0, "end": 2.5, "text": "Olá mundo este é um"},
            {"start": 2.5, "end": 4.0, "text": "teste"},
        ],
    }
    json_path = tmp_path / "video.json"
    json_path.write_text(json.dumps(payload), encoding="utf-8")
    return json_path
