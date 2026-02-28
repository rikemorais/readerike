"""FFmpegAudioExtractor — extracts audio from video using FFmpeg."""

import logging
from pathlib import Path

import ffmpeg

from readerike.core.entities.video import Video
from readerike.core.exceptions import AudioExtractionError
from readerike.core.ports.audio_extractor import IAudioExtractor

logger = logging.getLogger(__name__)

# Audio settings optimised for Whisper: 16kHz mono WAV
_SAMPLE_RATE = 16_000
_CHANNELS = 1
_CODEC = "pcm_s16le"


class FFmpegAudioExtractor(IAudioExtractor):
    """Implements IAudioExtractor using the ffmpeg-python library.

    Produces a 16 kHz mono WAV file, which is the format recommended by
    OpenAI Whisper for best accuracy and lowest memory usage.
    """

    def extract(self, video: Video, output_path: Path) -> Path:
        """Extract audio from *video* and write a 16 kHz mono WAV to *output_path*.

        Args:
            video: Source video entity (path must exist).
            output_path: Target path for the extracted audio.

        Returns:
            The resolved path of the written audio file.

        Raises:
            AudioExtractionError: On any FFmpeg failure.
        """
        # Force .wav extension so downstream tools receive a valid format
        output_path = output_path.with_suffix(".wav")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.debug(
            "FFmpeg extracting audio: %s → %s (sr=%d, ch=%d)",
            video.path,
            output_path,
            _SAMPLE_RATE,
            _CHANNELS,
        )

        try:
            (
                ffmpeg.input(str(video.path))
                .output(
                    str(output_path),
                    ar=_SAMPLE_RATE,
                    ac=_CHANNELS,
                    acodec=_CODEC,
                )
                .overwrite_output()
                .run(quiet=True)
            )
        except ffmpeg.Error as exc:
            stderr = exc.stderr.decode() if exc.stderr else "no stderr"
            raise AudioExtractionError(
                f"FFmpeg failed to extract audio from {video.path}: {stderr}"
            ) from exc

        return output_path
