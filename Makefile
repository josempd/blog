.DEFAULT_GOAL := help
SHELL := /bin/bash

DC  := docker compose
RUN := $(DC) exec backend
DB  := $(DC) exec db

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

.PHONY: up
up: ## Start all services (detached)
	$(DC) up -d

.PHONY: down
down: ## Stop all services
	$(DC) down

.PHONY: build
build: ## Rebuild backend image
	$(DC) build backend

.PHONY: restart
restart: ## Restart backend (keeps DB running)
	$(DC) restart backend

.PHONY: logs
logs: ## Tail backend logs
	$(DC) logs -f backend

.PHONY: logs-all
logs-all: ## Tail all service logs
	$(DC) logs -f

.PHONY: ps
ps: ## Show running services
	$(DC) ps

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

.PHONY: shell
shell: ## Shell into backend container
	$(RUN) bash

.PHONY: dbshell
dbshell: ## psql into the database
	$(DB) psql -U $${POSTGRES_USER:-postgres} -d $${POSTGRES_DB:-app}

# ---------------------------------------------------------------------------
# Code quality
# ---------------------------------------------------------------------------

.PHONY: lint
lint: ## Run ty + ruff checks
	$(RUN) bash scripts/lint.sh

.PHONY: fmt
fmt: ## Auto-format with ruff
	$(RUN) bash scripts/format.sh

.PHONY: check
check: lint test ## Lint + test (CI equivalent)

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

.PHONY: test
test: ## Run pytest with coverage
	$(RUN) bash scripts/tests-start.sh

.PHONY: test-fast
test-fast: ## Run pytest without coverage (faster)
	$(RUN) pytest tests/ -x -q

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

.PHONY: migrate
migrate: ## Generate alembic migration (usage: make migrate m="add post model")
	$(RUN) alembic -c app/alembic.ini revision --autogenerate -m "$(m)"

.PHONY: upgrade
upgrade: ## Apply all pending migrations
	$(RUN) alembic -c app/alembic.ini upgrade head

.PHONY: downgrade
downgrade: ## Rollback one migration
	$(RUN) alembic -c app/alembic.ini downgrade -1

.PHONY: db-reset
db-reset: ## Drop and recreate the database (destructive!)
	$(DC) down -v
	$(DC) up -d db
	@echo "Waiting for DB..."
	@sleep 3
	$(DC) up -d

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

.PHONY: lock
lock: ## Regenerate uv.lock
	cd backend && uv lock

.PHONY: install
install: ## Install backend deps locally (for IDE support)
	cd backend && uv sync --all-groups

.PHONY: setup
setup: install ## Full dev setup (deps + pre-commit hooks)
	pre-commit install

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
