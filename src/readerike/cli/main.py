"""CLI for readerike — transcribe videos from the command line."""

from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from readerike.adapters.ffmpeg_extractor import FFmpegAudioExtractor
from readerike.adapters.file_repository import FileTranscriptionRepository
from readerike.adapters.whisper_transcriber import WhisperTranscriber
from readerike.core.use_cases.transcribe_video import TranscribeVideoUseCase
from readerike.infrastructure.config import settings
from readerike.infrastructure.logging_setup import configure_logging

console = Console()


@click.command()
@click.argument("video", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory for the output JSON. Defaults to READERIKE_OUTPUT_DIR or ./outputs.",
)
@click.option(
    "--language",
    "-l",
    default=None,
    help="Language hint (e.g. 'pt', 'en'). Auto-detected when omitted.",
)
@click.option(
    "--model",
    "-m",
    default=None,
    help="Whisper model size (tiny/base/small/medium/large). Defaults to READERIKE_WHISPER_MODEL.",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging.")
def app(
    video: Path,
    output_dir: Path | None,
    language: str | None,
    model: str | None,
    verbose: bool,
) -> None:
    """Transcribe a VIDEO file using Whisper and save the result as JSON."""
    configure_logging("DEBUG" if verbose else settings.log_level)

    resolved_output = output_dir or settings.output_dir
    resolved_model = model or settings.whisper_model

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task("Loading Whisper model…", total=None)
        transcriber = WhisperTranscriber(model_name=resolved_model, device=settings.whisper_device)

    use_case = TranscribeVideoUseCase(
        audio_extractor=FFmpegAudioExtractor(),
        transcriber=transcriber,
        repository=FileTranscriptionRepository(),
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(f"Transcribing {video.name}…", total=None)
        transcription = use_case.execute(video, resolved_output, language)

    console.print(f"\n[bold green]Done![/bold green] {transcription.word_count} words transcribed.")
    console.print(f"Language: [cyan]{transcription.language}[/cyan]")
    preview = transcription.text[:500]
    suffix = "…" if len(transcription.text) > 500 else ""
    console.print(f"\n[dim]{preview}{suffix}[/dim]")
