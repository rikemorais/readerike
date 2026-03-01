"""Jobs REST router."""

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse, Response

from readerike.adapters.sqlite_job_repository import SQLiteJobRepository
from readerike.api.dependencies import get_job_repository, get_settings, get_use_case
from readerike.api.routers.ws import broadcast
from readerike.api.schemas.job import JobCreateResponse, JobListItem, JobResponse, SegmentResponse, TranscriptionResponse
from readerike.core.entities.job import Job, JobStatus
from readerike.core.use_cases.transcribe_video import TranscribeVideoUseCase
from readerike.infrastructure.config import Settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs")

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}


def _job_to_response(job: Job) -> JobResponse:
    transcription_resp = None
    if job.transcription:
        transcription_resp = TranscriptionResponse(
            text=job.transcription.text,
            language=job.transcription.language,
            model_name=job.transcription.model_name,
            segments=[
                SegmentResponse(start=s.start, end=s.end, text=s.text)
                for s in job.transcription.segments
            ],
        )
    return JobResponse(
        id=job.id,
        video_filename=job.video_filename,
        language=job.language,
        model_name=job.model_name,
        status=job.status,
        created_at=job.created_at,
        completed_at=job.completed_at,
        error=job.error,
        transcription=transcription_resp,
    )


async def _run_transcription(
    job: Job,
    repo: SQLiteJobRepository,
    use_case: TranscribeVideoUseCase,
    output_dir: Path,
) -> None:
    """Background task: run the full transcription pipeline and update job status."""
    try:
        processing_job = Job(
            id=job.id,
            video_filename=job.video_filename,
            video_path=job.video_path,
            language=job.language,
            model_name=job.model_name,
            status=JobStatus.PROCESSING,
            created_at=job.created_at,
        )
        await repo.save(processing_job)
        await broadcast(job.id, {"event": "progress", "step": "extracting_audio", "pct": 10})

        await broadcast(job.id, {"event": "progress", "step": "extracting_audio", "pct": 30})

        transcription = use_case.execute(
            video_path=job.video_path,
            output_dir=output_dir,
            language=job.language,
        )

        await broadcast(job.id, {"event": "progress", "step": "transcribing", "pct": 90})

        completed_job = Job(
            id=job.id,
            video_filename=job.video_filename,
            video_path=job.video_path,
            language=job.language,
            model_name=job.model_name,
            status=JobStatus.COMPLETED,
            created_at=job.created_at,
            completed_at=datetime.now(timezone.utc),
            transcription=transcription,
        )
        await repo.save(completed_job)
        await broadcast(
            job.id,
            {"event": "completed", "job": _job_to_response(completed_job).model_dump(mode="json")},
        )
        logger.info("Job %s completed successfully", job.id)

    except Exception as exc:  # noqa: BLE001
        logger.exception("Job %s failed: %s", job.id, exc)
        failed_job = Job(
            id=job.id,
            video_filename=job.video_filename,
            video_path=job.video_path,
            language=job.language,
            model_name=job.model_name,
            status=JobStatus.FAILED,
            created_at=job.created_at,
            completed_at=datetime.now(timezone.utc),
            error=str(exc),
        )
        await repo.save(failed_job)
        await broadcast(job.id, {"event": "error", "message": str(exc)})


@router.post("", response_model=JobCreateResponse, status_code=201)
async def create_job(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    language: str | None = Query(default=None),
    model: str = Query(default="base"),
    repo: SQLiteJobRepository = Depends(get_job_repository),
    use_case: TranscribeVideoUseCase = Depends(get_use_case),
    settings: Settings = Depends(get_settings),
) -> JobCreateResponse:
    """Upload a video file and enqueue a transcription job."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    job_id = str(uuid.uuid4())
    upload_path = settings.upload_dir / f"{job_id}{suffix}"
    upload_path.parent.mkdir(parents=True, exist_ok=True)

    content = await file.read()
    upload_path.write_bytes(content)

    job = Job(
        id=job_id,
        video_filename=file.filename,
        video_path=upload_path,
        language=language,
        model_name=model,
        status=JobStatus.PENDING,
    )
    await repo.save(job)

    background_tasks.add_task(
        _run_transcription,
        job=job,
        repo=repo,
        use_case=use_case,
        output_dir=settings.output_dir,
    )

    return JobCreateResponse(
        id=job_id,
        status=JobStatus.PENDING,
        message="Job enqueued. Connect to the WebSocket for live updates.",
    )


@router.get("", response_model=list[JobListItem])
async def list_jobs(
    repo: SQLiteJobRepository = Depends(get_job_repository),
) -> list[JobListItem]:
    """Return all jobs (without transcription data)."""
    jobs = await repo.find_all()
    return [
        JobListItem(
            id=j.id,
            video_filename=j.video_filename,
            language=j.language,
            model_name=j.model_name,
            status=j.status,
            created_at=j.created_at,
            completed_at=j.completed_at,
            error=j.error,
        )
        for j in jobs
    ]


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    repo: SQLiteJobRepository = Depends(get_job_repository),
) -> JobResponse:
    """Return full job details including transcription."""
    job = await repo.find_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_response(job)


@router.delete("/{job_id}", status_code=204)
async def delete_job(
    job_id: str,
    repo: SQLiteJobRepository = Depends(get_job_repository),
) -> None:
    """Remove a job and its uploaded video file."""
    job = await repo.find_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.video_path.exists():
        job.video_path.unlink()
    await repo.delete(job_id)


@router.get("/{job_id}/download")
async def download_transcription(
    job_id: str,
    format: str = Query(default="json", pattern="^(json|txt|srt)$"),
    repo: SQLiteJobRepository = Depends(get_job_repository),
) -> Response:
    """Download the transcription in the requested format."""
    job = await repo.find_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.COMPLETED or job.transcription is None:
        raise HTTPException(status_code=409, detail="Transcription not yet available")

    stem = Path(job.video_filename).stem

    if format == "json":
        import json as _json

        payload = {
            "id": job.id,
            "video_filename": job.video_filename,
            "language": job.transcription.language,
            "model_name": job.transcription.model_name,
            "text": job.transcription.text,
            "segments": [
                {"start": s.start, "end": s.end, "text": s.text}
                for s in job.transcription.segments
            ],
        }
        content = _json.dumps(payload, ensure_ascii=False, indent=2)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{stem}.json"'},
        )

    if format == "txt":
        return Response(
            content=job.transcription.text,
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{stem}.txt"'},
        )

    # SRT
    lines: list[str] = []
    for i, seg in enumerate(job.transcription.segments, start=1):
        start_tc = _seconds_to_srt(seg.start)
        end_tc = _seconds_to_srt(seg.end)
        lines.append(f"{i}\n{start_tc} --> {end_tc}\n{seg.text.strip()}\n")
    srt_content = "\n".join(lines)
    return Response(
        content=srt_content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{stem}.srt"'},
    )


def _seconds_to_srt(seconds: float) -> str:
    """Convert float seconds to SRT timestamp HH:MM:SS,mmm."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
