"""Integration tests for the /api/v1/jobs REST router."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from readerike.adapters.sqlite_job_repository import SQLiteJobRepository
from readerike.api.app import create_app
from readerike.api.dependencies import get_job_repository, get_settings, get_use_case
from readerike.core.entities.job import Job, JobStatus
from readerike.core.entities.transcription import Transcription, TranscriptionSegment
from readerike.infrastructure.config import Settings

# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_settings(tmp_path: Path) -> Settings:
    return Settings(
        upload_dir=tmp_path / "uploads",
        output_dir=tmp_path / "output",
        db_path=tmp_path / "test.db",
    )


def _make_mp4_bytes() -> bytes:
    """Return a minimal non-empty bytes object posing as a video file."""
    return b"\x00" * 512


def _make_completed_job(tmp_path: Path) -> Job:
    tx = Transcription(
        video_path=tmp_path / "vid.mp4",
        text="Hello world",
        segments=[TranscriptionSegment(start=0.0, end=1.5, text="Hello world")],
        language="en",
        model_name="base",
    )
    return Job(
        id="test-job-id",
        video_filename="vid.mp4",
        video_path=tmp_path / "vid.mp4",
        model_name="base",
        status=JobStatus.COMPLETED,
        created_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
        completed_at=datetime(2024, 6, 1, 1, tzinfo=timezone.utc),
        transcription=tx,
    )


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
async def repo(tmp_path: Path) -> SQLiteJobRepository:
    r = SQLiteJobRepository(db_path=tmp_path / "test.db")
    await r.initialize()
    return r


@pytest.fixture()
def mock_use_case() -> MagicMock:
    """A use case that raises immediately so background tasks fail fast."""
    uc = MagicMock()
    uc.execute.side_effect = RuntimeError("stub — not a real transcription")
    return uc


@pytest.fixture()
async def client(
    tmp_path: Path,
    repo: SQLiteJobRepository,
    mock_use_case: MagicMock,
) -> AsyncClient:
    settings = _make_settings(tmp_path)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)

    app = create_app()

    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_job_repository] = lambda: repo
    app.dependency_overrides[get_use_case] = lambda: mock_use_case

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.integration
class TestCreateJob:
    async def test_returns_201_with_job_id(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/jobs",
            files={"file": ("video.mp4", _make_mp4_bytes(), "video/mp4")},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert data["status"] == "pending"

    async def test_rejects_unsupported_extension(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/jobs",
            files={"file": ("document.txt", b"hello", "text/plain")},
        )

        assert resp.status_code == 400
        assert "Unsupported file type" in resp.json()["detail"]

    async def test_rejects_missing_filename(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/jobs",
            files={"file": ("", b"data", "video/mp4")},
        )

        # FastAPI returns 422 when the multipart part has no filename
        # because Starlette does not parse it as a valid UploadFile.
        assert resp.status_code in (400, 422)

    async def test_accepts_language_query_param(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/jobs?language=pt",
            files={"file": ("vid.mp4", _make_mp4_bytes(), "video/mp4")},
        )

        assert resp.status_code == 201

    async def test_accepts_model_query_param(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/jobs?model=small",
            files={"file": ("vid.mp4", _make_mp4_bytes(), "video/mp4")},
        )

        assert resp.status_code == 201

    async def test_background_task_failure_sets_job_failed(
        self, client: AsyncClient, repo: SQLiteJobRepository
    ) -> None:
        resp = await client.post(
            "/api/v1/jobs",
            files={"file": ("vid.mp4", _make_mp4_bytes(), "video/mp4")},
        )
        assert resp.status_code == 201
        job_id = resp.json()["id"]

        job = await repo.find_by_id(job_id)
        assert job is not None
        assert job.status == JobStatus.FAILED
        assert job.error is not None
        assert "stub" in job.error


@pytest.mark.integration
class TestListJobs:
    async def test_returns_empty_list_initially(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/jobs")

        assert resp.status_code == 200
        assert resp.json() == []

    async def test_returns_job_after_creation(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/jobs",
            files={"file": ("vid.mp4", _make_mp4_bytes(), "video/mp4")},
        )

        resp = await client.get("/api/v1/jobs")

        assert resp.status_code == 200
        jobs = resp.json()
        assert len(jobs) == 1
        assert jobs[0]["video_filename"] == "vid.mp4"
        assert jobs[0]["status"] == "failed"


@pytest.mark.integration
class TestGetJob:
    async def test_returns_404_for_unknown_id(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/jobs/nonexistent-id")

        assert resp.status_code == 404

    async def test_returns_job_details(
        self, client: AsyncClient, tmp_path: Path, repo: SQLiteJobRepository
    ) -> None:
        job = _make_completed_job(tmp_path)
        await repo.save(job)

        resp = await client.get(f"/api/v1/jobs/{job.id}")

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == job.id
        assert data["status"] == "completed"
        assert data["transcription"]["text"] == "Hello world"

    async def test_includes_transcription_segments(
        self, client: AsyncClient, tmp_path: Path, repo: SQLiteJobRepository
    ) -> None:
        job = _make_completed_job(tmp_path)
        await repo.save(job)

        resp = await client.get(f"/api/v1/jobs/{job.id}")

        segments = resp.json()["transcription"]["segments"]
        assert len(segments) == 1
        assert segments[0]["text"] == "Hello world"


@pytest.mark.integration
class TestDeleteJob:
    async def test_returns_204(
        self, client: AsyncClient, tmp_path: Path, repo: SQLiteJobRepository
    ) -> None:
        video_file = tmp_path / "test-job-id.mp4"
        video_file.write_bytes(b"\x00")
        job = Job(
            id="test-job-id",
            video_filename="vid.mp4",
            video_path=video_file,
            model_name="base",
            status=JobStatus.PENDING,
            created_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
        )
        await repo.save(job)

        resp = await client.delete(f"/api/v1/jobs/{job.id}")

        assert resp.status_code == 204
        assert not video_file.exists()

    async def test_job_no_longer_listed_after_delete(
        self, client: AsyncClient, tmp_path: Path, repo: SQLiteJobRepository
    ) -> None:
        video_file = tmp_path / "del-test.mp4"
        video_file.write_bytes(b"\x00")
        job = Job(
            id="del-test",
            video_filename="del.mp4",
            video_path=video_file,
            model_name="base",
            status=JobStatus.PENDING,
            created_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
        )
        await repo.save(job)
        await client.delete(f"/api/v1/jobs/{job.id}")

        resp = await client.get("/api/v1/jobs")
        ids = [j["id"] for j in resp.json()]
        assert "del-test" not in ids

    async def test_returns_404_for_unknown_id(self, client: AsyncClient) -> None:
        resp = await client.delete("/api/v1/jobs/does-not-exist")

        assert resp.status_code == 404


@pytest.mark.integration
class TestDownloadTranscription:
    async def test_returns_404_when_job_missing(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/jobs/missing/download?format=json")
        assert resp.status_code == 404

    async def test_returns_409_when_not_completed(
        self, client: AsyncClient, tmp_path: Path, repo: SQLiteJobRepository
    ) -> None:
        job = Job(
            id="pending-job",
            video_filename="vid.mp4",
            video_path=tmp_path / "vid.mp4",
            model_name="base",
            status=JobStatus.PENDING,
            created_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
        )
        await repo.save(job)

        resp = await client.get(f"/api/v1/jobs/{job.id}/download?format=json")
        assert resp.status_code == 409

    async def test_download_json(
        self, client: AsyncClient, tmp_path: Path, repo: SQLiteJobRepository
    ) -> None:
        job = _make_completed_job(tmp_path)
        await repo.save(job)

        resp = await client.get(f"/api/v1/jobs/{job.id}/download?format=json")

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/json"
        assert 'filename="vid.json"' in resp.headers["content-disposition"]
        payload = resp.json()
        assert payload["text"] == "Hello world"

    async def test_download_txt(
        self, client: AsyncClient, tmp_path: Path, repo: SQLiteJobRepository
    ) -> None:
        job = _make_completed_job(tmp_path)
        await repo.save(job)

        resp = await client.get(f"/api/v1/jobs/{job.id}/download?format=txt")

        assert resp.status_code == 200
        assert "Hello world" in resp.text

    async def test_download_srt(
        self, client: AsyncClient, tmp_path: Path, repo: SQLiteJobRepository
    ) -> None:
        job = _make_completed_job(tmp_path)
        await repo.save(job)

        resp = await client.get(f"/api/v1/jobs/{job.id}/download?format=srt")

        assert resp.status_code == 200
        assert "00:00:00,000 --> 00:00:01,500" in resp.text
        assert "Hello world" in resp.text

    async def test_download_invalid_format_returns_422(
        self, client: AsyncClient, tmp_path: Path, repo: SQLiteJobRepository
    ) -> None:
        job = _make_completed_job(tmp_path)
        await repo.save(job)

        resp = await client.get(f"/api/v1/jobs/{job.id}/download?format=xml")
        assert resp.status_code == 422
