.PHONY: setup dev test lint typecheck docker-up worker migrate reset

setup:
	python -m venv .venv || true
	.venv\Scripts\pip install --upgrade pip
	.venv\Scripts\pip install -r requirements.txt -r requirements-dev.txt

dev:
	.venv\Scripts\uvicorn app.main:app --reload --host ${HOST} --port ${PORT}

test:
	.venv\Scripts\pytest -q

lint:
	.venv\Scripts\ruff check .

typecheck:
	.venv\Scripts\mypy app

docker-up:
	docker-compose up --build

docker-up-qdrant:
	docker-compose up -d qdrant redis

integration-test-qdrant:
	@echo "Starting Qdrant + Redis (detached)..."
	docker-compose up -d qdrant redis
	.venv\Scripts\pytest tests/test_qdrant_integration.py -q || (echo "Integration test failed"; exit 1)

worker:
	.venv\Scripts\python -m app.tasks.worker

migrate:
	python -c "from app.storage.db import init_db; init_db()"

reset:
	rm -rf data || rmdir /S /Q data || true
	python -c "from app.storage.db import init_db; init_db()"
