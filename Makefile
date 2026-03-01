.PHONY: install install-dev test test-unit test-integration lint format typecheck security clean api-dev frontend-dev docker-up help

PYTHON := python3
PIP    := pip

# ── Setup ────────────────────────────────────────────────────────────────────
install: ## Install production dependencies
	$(PIP) install -e .

install-dev: ## Install all dependencies including dev tools
	$(PIP) install -e ".[dev]"
	pre-commit install

# ── Tests ────────────────────────────────────────────────────────────────────
test: ## Run all tests with coverage
	pytest

test-unit: ## Run only unit tests
	pytest -m unit tests/unit/

test-integration: ## Run only integration tests (requires FFmpeg + Whisper model)
	pytest -m integration tests/integration/

test-watch: ## Run tests in watch mode
	pytest --tb=short -q --no-header -rN --co

# ── Code Quality ─────────────────────────────────────────────────────────────
lint: ## Check code style and quality
	ruff check src/ tests/

format: ## Auto-format code
	ruff format src/ tests/
	ruff check --fix src/ tests/

typecheck: ## Run static type checking
	mypy src/

# ── Security ─────────────────────────────────────────────────────────────────
security: ## Run security checks
	bandit -r src/ -ll
	safety check

# ── Utilities ────────────────────────────────────────────────────────────────
clean: ## Remove build artifacts and cache files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage dist build *.egg-info

api-dev: ## Run the FastAPI dev server
	uvicorn readerike.api.app:app --reload --host 0.0.0.0 --port 8000

frontend-dev: ## Run the Next.js dev server
	cd frontend && npm run dev

docker-up: ## Start all services via Docker Compose
	docker compose up --build

ci: lint typecheck security test ## Run all CI checks locally

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
