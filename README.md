# Nova Agent Runtime

A set of status badges — replace <OWNER> and <REPO> with your GitHub repo.

[![CI](https://github.com/dmitriy718/power-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/dmitriy718/power-harness/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-pytest-blue)](#)
[![Lint](https://img.shields.io/badge/lint-ruff%20%7C%20mypy-orange)](#)

A durable FastAPI + LangGraph agent runtime for local and cloud AI development.

How to show the CI badge for your repository:

1. Replace `<OWNER>` and `<REPO>` in the CI badge URL above with your GitHub organization/user and repository name.
2. Example badge markdown (replace values):

```markdown
[![CI](https://github.com/dmitriy718/power-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/dmitriy718/power-harness/actions/workflows/ci.yml)
```

If you prefer shields.io:

```markdown
[![CI](https://img.shields.io/github/actions/workflow/status/dmitriy718/power-harness/ci.yml?branch=main)](https://github.com/dmitriy718/power-harness/actions/workflows/ci.yml)
```

## Features

- FastAPI API with task and memory endpoints (stubs)
- Layered memory store (SQLite + Qdrant stub)
- Tool registry and safe tools (filesystem, shell, memory)
- Celery-based task queue and worker stub
- Docker Compose orchestration for api, worker, redis, qdrant, postgres
- Tests with pytest
- Linting and typing with ruff and mypy

## Windows 11 setup

1. Install Python 3.11
2. Open PowerShell and run:

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -U pip
.\.venv\Scripts\pip install -r requirements.txt -r requirements-dev.txt
```

3. Initialize DB and run dev server:

```powershell
make migrate
make dev
```

## Ollama setup

Install Ollama (https://ollama.ai) and run local endpoint. Then set `.env` values:

```
PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=qwen3:latest
```

## Qdrant setup

Use docker-compose or install qdrant locally and set `QDRANT_URL` in `.env`:

```
QDRANT_URL=http://localhost:6333
```

## Redis setup

Use a local Redis instance or Docker and set `REDIS_URL` in `.env`:

```
REDIS_URL=redis://localhost:6379/0
```

## Dry run mode

The runtime supports `DRY_RUN=true` for local development without a real provider.
Default behavior is dry-run if the configured provider lacks a model or API credentials.

## Running API

```powershell
make dev
# or via docker
make docker-up
```

## Running worker

```powershell
make worker
```

## Testing

```powershell
make test
```

## Developer tooling

Install and enable pre-commit hooks to run linters and type checks locally:

```powershell
.venv\Scripts\pip install pre-commit
pre-commit install
pre-commit run --all-files
```


## Continuous integration

A GitHub Actions workflow is included at `.github/workflows/ci.yml`.
It installs dependencies, runs `ruff`, `mypy`, and `pytest` with `DRY_RUN=true`.

## Switching model providers

Set `PROVIDER` to one of: `ollama`, `openai`, `openrouter`, `custom`.

## Adding new tools

Register new tools in `app.tools.registry.registry.register("name", fn)`.

## Memory design & safety

See `app/memory` for storage and extractor. Tools have safety checks and dry-run support.

## Limitations

This scaffold includes minimal implementations and stubs (Qdrant, LangGraph, LangChain integrations). Extend with real providers and robust worker orchestration for production.
