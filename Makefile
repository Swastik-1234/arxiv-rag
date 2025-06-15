.PHONY: help start stop restart build status logs health clean setup format lint test

help:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  arXiv RAG — Commands"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  make start      Start all services"
	@echo "  make stop       Stop all services"
	@echo "  make restart    Restart all services"
	@echo "  make build      Rebuild all images"
	@echo "  make status     Show service status"
	@echo "  make logs       Tail all logs"
	@echo "  make health     Check API health"
	@echo "  make clean      Stop + remove all volumes"
	@echo "  make setup      Install Python dependencies"
	@echo "  make format     Format code"
	@echo "  make lint       Lint + type check"
	@echo "  make test       Run tests"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

start:
	docker compose up -d
	@echo ""
	@echo "✅ Services starting up — wait ~30s then check:"
	@echo "   API:      http://localhost:8000/docs"
	@echo "   Airflow:  http://localhost:8080"
	@echo "   Langfuse: http://localhost:3000"
	@echo "   Qdrant:   http://localhost:6333/dashboard"

stop:
	docker compose down

restart:
	docker compose down
	docker compose up -d

build:
	docker compose up --build -d

status:
	docker compose ps

logs:
	docker compose logs -f

logs-%:
	docker compose logs -f $*

health:
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "❌ API not reachable"

clean:
	docker compose down --volumes --remove-orphans
	@echo "⚠️  All volumes deleted."

setup:
	uv sync --extra dev

format:
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

lint:
	uv run ruff check src/ tests/
	uv run mypy src/

test:
	uv run pytest tests/ -v

test-cov:
	uv run pytest tests/ -v --cov=src --cov-report=term-missing
