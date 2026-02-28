# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

# System deps for building Python packages and ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only dependency manifests first (layer cache optimisation)
COPY pyproject.toml ./
COPY src/readerike/__init__.py src/readerike/__init__.py

# Install dependencies into an isolated prefix
RUN pip install --no-cache-dir --prefix=/install -e ".[dev]" || \
    pip install --no-cache-dir --prefix=/install -e .


# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="readerike" \
      org.opencontainers.image.description="Video transcription tool powered by Whisper and FFmpeg" \
      org.opencontainers.image.source="https://github.com/rikemorais/readerike"

# Runtime system deps (FFmpeg is mandatory)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY src/ src/
COPY pyproject.toml ./

# Install the package itself (without deps, already copied above)
RUN pip install --no-cache-dir --no-deps -e .

# Whisper downloads models to ~/.cache/whisper — persist via volume
ENV WHISPER_MODEL_DIR=/models
RUN mkdir -p /models && chown appuser:appuser /models

# Output directory for transcriptions
RUN mkdir -p /output && chown appuser:appuser /output

USER appuser

# Default: show help; override with `docker run ... readerike transcribe video.mp4`
ENTRYPOINT ["readerike"]
CMD ["--help"]
