"""Unit tests for SQLiteJobRepository."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from readerike.adapters.sqlite_job_repository import SQLiteJobRepository
from readerike.core.entities.job import Job, JobStatus
from readerike.core.entities.transcription import Transcription, TranscriptionSegment


def _make_job(
    tmp_path: Path,
    *,
    job_id: str = "job-1",
    status: JobStatus = JobStatus.PENDING,
    created_at: datetime | None = None,
) -> Job:
    return Job(
        id=job_id,
        video_filename="sample.mp4",
        video_path=tmp_path / "sample.mp4",
        language="pt",
        model_name="base",
        status=status,
        created_at=created_at or datetime(2024, 1, 1, tzinfo=timezone.utc),
    )


def _make_transcription(tmp_path: Path) -> Transcription:
    return Transcription(
        video_path=tmp_path / "sample.mp4",
        text="Olá mundo",
        segments=[TranscriptionSegment(start=0.0, end=2.0, text="Olá mundo")],
        language="pt",
        model_name="base",
    )


@pytest.mark.unit
class TestSQLiteJobRepository:
    @pytest.fixture()
    async def repo(self, tmp_path: Path) -> SQLiteJobRepository:
        r = SQLiteJobRepository(db_path=tmp_path / "test.db")
        await r.initialize()
        return r

    async def test_save_and_find_by_id(self, repo: SQLiteJobRepository, tmp_path: Path) -> None:
        job = _make_job(tmp_path)
        await repo.save(job)

        fetched = await repo.find_by_id("job-1")

        assert fetched is not None
        assert fetched.id == "job-1"
        assert fetched.video_filename == "sample.mp4"
        assert fetched.status == JobStatus.PENDING
        assert fetched.language == "pt"

    async def test_find_by_id_returns_none_for_missing(
        self, repo: SQLiteJobRepository
    ) -> None:
        result = await repo.find_by_id("nonexistent")
        assert result is None

    async def test_save_upserts_status(self, repo: SQLiteJobRepository, tmp_path: Path) -> None:
        job = _make_job(tmp_path)
        await repo.save(job)

        updated = Job(
            id=job.id,
            video_filename=job.video_filename,
            video_path=job.video_path,
            language=job.language,
            model_name=job.model_name,
            status=JobStatus.PROCESSING,
            created_at=job.created_at,
        )
        await repo.save(updated)

        fetched = await repo.find_by_id("job-1")
        assert fetched is not None
        assert fetched.status == JobStatus.PROCESSING

    async def test_find_all_returns_all_saved_jobs(
        self, repo: SQLiteJobRepository, tmp_path: Path
    ) -> None:
        await repo.save(_make_job(tmp_path, job_id="a"))
        await repo.save(_make_job(tmp_path, job_id="b"))

        jobs = await repo.find_all()

        ids = {j.id for j in jobs}
        assert ids == {"a", "b"}

    async def test_find_all_ordered_by_created_at_desc(
        self, repo: SQLiteJobRepository, tmp_path: Path
    ) -> None:
        older = _make_job(
            tmp_path, job_id="old", created_at=datetime(2024, 1, 1, tzinfo=timezone.utc)
        )
        newer = _make_job(
            tmp_path, job_id="new", created_at=datetime(2024, 6, 1, tzinfo=timezone.utc)
        )
        await repo.save(older)
        await repo.save(newer)

        jobs = await repo.find_all()

        assert jobs[0].id == "new"
        assert jobs[1].id == "old"

    async def test_find_all_empty_returns_empty_list(
        self, repo: SQLiteJobRepository
    ) -> None:
        assert await repo.find_all() == []

    async def test_delete_removes_job(self, repo: SQLiteJobRepository, tmp_path: Path) -> None:
        job = _make_job(tmp_path)
        await repo.save(job)
        await repo.delete("job-1")

        assert await repo.find_by_id("job-1") is None

    async def test_delete_nonexistent_does_not_raise(
        self, repo: SQLiteJobRepository
    ) -> None:
        await repo.delete("does-not-exist")  # should not raise

    async def test_save_with_transcription_round_trips(
        self, repo: SQLiteJobRepository, tmp_path: Path
    ) -> None:
        transcription = _make_transcription(tmp_path)
        job = Job(
            id="job-with-tx",
            video_filename="sample.mp4",
            video_path=tmp_path / "sample.mp4",
            model_name="base",
            status=JobStatus.COMPLETED,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            completed_at=datetime(2024, 1, 1, 1, tzinfo=timezone.utc),
            transcription=transcription,
        )
        await repo.save(job)

        fetched = await repo.find_by_id("job-with-tx")

        assert fetched is not None
        assert fetched.transcription is not None
        assert fetched.transcription.text == "Olá mundo"
        assert fetched.transcription.language == "pt"
        assert len(fetched.transcription.segments) == 1
        assert fetched.transcription.segments[0].start == pytest.approx(0.0)
        assert fetched.transcription.segments[0].end == pytest.approx(2.0)

    async def test_created_at_preserves_timezone(
        self, repo: SQLiteJobRepository, tmp_path: Path
    ) -> None:
        ts = datetime(2024, 3, 15, 12, 30, 0, tzinfo=timezone.utc)
        job = _make_job(tmp_path, job_id="tz-job", created_at=ts)
        await repo.save(job)

        fetched = await repo.find_by_id("tz-job")

        assert fetched is not None
        assert fetched.created_at.tzinfo is not None
        assert fetched.created_at == ts

    async def test_save_failed_job_stores_error(
        self, repo: SQLiteJobRepository, tmp_path: Path
    ) -> None:
        job = Job(
            id="job-fail",
            video_filename="sample.mp4",
            video_path=tmp_path / "sample.mp4",
            model_name="base",
            status=JobStatus.FAILED,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            completed_at=datetime(2024, 1, 1, 1, tzinfo=timezone.utc),
            error="ffmpeg not found",
        )
        await repo.save(job)

        fetched = await repo.find_by_id("job-fail")

        assert fetched is not None
        assert fetched.error == "ffmpeg not found"
        assert fetched.status == JobStatus.FAILED
