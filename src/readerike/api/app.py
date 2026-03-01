"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from readerike.api.dependencies import get_job_repository, get_settings
from readerike.api.routers import jobs as jobs_router
from readerike.api.routers import ws as ws_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    repo = get_job_repository()
    await repo.initialize()
    logger.info("Database ready at %s", settings.db_path)
    yield
    logger.info("Shutting down readerike API")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="readerike API",
        description="Video transcription API powered by OpenAI Whisper",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(settings.upload_dir)), name="uploads")

    app.include_router(jobs_router.router, prefix="/api/v1")
    app.include_router(ws_router.router, prefix="/api/v1")

    return app


app = create_app()
