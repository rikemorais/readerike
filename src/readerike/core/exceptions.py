"""Domain exceptions — typed errors for each failure mode in the core."""


class ReaderIkeError(Exception):
    """Base exception for all readerike errors."""


class AudioExtractionError(ReaderIkeError):
    """Raised when audio extraction from a video file fails."""


class TranscriptionError(ReaderIkeError):
    """Raised when a transcription engine fails to process audio."""


class RepositoryError(ReaderIkeError):
    """Raised when persisting or retrieving a transcription fails."""
