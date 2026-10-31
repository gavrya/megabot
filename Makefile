.DEFAULT_GOAL := help
.PHONY: help install run lint format typecheck check migrate migration rollback seed up down logs

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies into .venv
	uv sync

run: ## Run the API with autoreload
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint: ## Lint the code
	uv run ruff check .

format: ## Format the code and apply safe fixes
	uv run ruff format .
	uv run ruff check . --fix

typecheck: ## Type-check the code with pyright
	uv run pyright

check: ## Lint + format + type check without writing files (CI)
	uv run ruff check .
	uv run ruff format --check .
	uv run pyright

migration: ## Autogenerate a migration from the entities: make migration m="add x"
	uv run alembic revision --autogenerate -m "$(m)"

migrate: ## Apply all pending migrations
	uv run alembic upgrade head

rollback: ## Roll back the last migration
	uv run alembic downgrade -1

seed: ## Run all seeders
	uv run seed

up: ## Start the full stack with docker compose
	docker compose up -d --build

down: ## Stop the stack
	docker compose down

logs: ## Tail app logs
	docker compose logs -f app
