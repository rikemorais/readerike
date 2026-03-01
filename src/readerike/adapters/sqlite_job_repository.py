"""SQLiteJobRepository — async SQLite implementation of IJobRepository."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

from readerike.core.entities.job import Job, JobStatus
from readerike.core.entities.transcription import Transcription, TranscriptionSegment
from readerike.core.ports.job_repository import IJobRepository

logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS jobs (
    id                TEXT PRIMARY KEY,
    video_filename    TEXT NOT NULL,
    video_path        TEXT NOT NULL,
    language          TEXT,
    model_name        TEXT NOT NULL DEFAULT 'base',
    status            TEXT NOT NULL DEFAULT 'pending',
    created_at        TEXT NOT NULL,
    completed_at      TEXT,
    error             TEXT,
    transcription_json TEXT
)
"""


def _parse_dt(value: str | None) -> datetime | None:
    if value is None:
        return None
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _row_to_job(row: aiosqlite.Row) -> Job:
    transcription: Transcription | None = None
    raw_json = row["transcription_json"]
    if raw_json:
        payload = json.loads(raw_json)
        segments = [
            TranscriptionSegment(start=s["start"], end=s["end"], text=s["text"])
            for s in payload.get("segments", [])
        ]
        transcription = Transcription(
            video_path=Path(payload["video_path"]),
            text=payload.get("text", ""),
            segments=segments,
            language=payload.get("language", "unknown"),
            model_name=payload.get("model_name", "unknown"),
            created_at=_parse_dt(payload.get("created_at")) or datetime.now(timezone.utc),
        )

    return Job(
        id=row["id"],
        video_filename=row["video_filename"],
        video_path=Path(row["video_path"]),
        language=row["language"],
        model_name=row["model_name"],
        status=JobStatus(row["status"]),
        created_at=_parse_dt(row["created_at"]) or datetime.now(timezone.utc),
        completed_at=_parse_dt(row["completed_at"]),
        error=row["error"],
        transcription=transcription,
    )


def _transcription_to_json(transcription: Transcription) -> str:
    payload = {
        "video_path": str(transcription.video_path),
        "text": transcription.text,
        "language": transcription.language,
        "model_name": transcription.model_name,
        "created_at": transcription.created_at.isoformat(),
        "segments": [
            {"start": seg.start, "end": seg.end, "text": seg.text}
            for seg in transcription.segments
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


class SQLiteJobRepository(IJobRepository):
    """Async SQLite-backed job repository using aiosqlite."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self) -> None:
        """Create the jobs table if it doesn't exist."""
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(CREATE_TABLE_SQL)
            await db.commit()
        logger.debug("SQLiteJobRepository initialized at %s", self._db_path)

    async def save(self, job: Job) -> Job:
        transcription_json = (
            _transcription_to_json(job.transcription) if job.transcription else None
        )
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                INSERT INTO jobs (id, video_filename, video_path, language, model_name,
                                  status, created_at, completed_at, error, transcription_json)
                VALUES (:id, :video_filename, :video_path, :language, :model_name,
                        :status, :created_at, :completed_at, :error, :transcription_json)
                ON CONFLICT(id) DO UPDATE SET
                    status             = excluded.status,
                    completed_at       = excluded.completed_at,
                    error              = excluded.error,
                    transcription_json = excluded.transcription_json
                """,
                {
                    "id": job.id,
                    "video_filename": job.video_filename,
                    "video_path": str(job.video_path),
                    "language": job.language,
                    "model_name": job.model_name,
                    "status": job.status.value,
                    "created_at": job.created_at.isoformat(),
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "error": job.error,
                    "transcription_json": transcription_json,
                },
            )
            await db.commit()
        logger.debug("Saved job %s (status=%s)", job.id, job.status)
        return job

    async def find_by_id(self, job_id: str) -> Job | None:
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)) as cursor:
                row = await cursor.fetchone()
        if row is None:
            return None
        return _row_to_job(row)

    async def find_all(self) -> list[Job]:
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC"
            ) as cursor:
                rows = await cursor.fetchall()
        return [_row_to_job(row) for row in rows]

    async def delete(self, job_id: str) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
            await db.commit()
        logger.debug("Deleted job %s", job_id)
