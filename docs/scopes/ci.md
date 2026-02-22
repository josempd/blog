# scope: ci

CI/CD and build tooling — GitHub Actions workflows, Docker, compose files, dev scripts, Makefile, and pre-commit hooks.

## Key Files

```
.github/
  workflows/ci.yml         # Lint + test on push/PR
  workflows/labeler.yml    # Auto-label PRs by scope, enforce labels
  labeler.yml              # Path → scope:label mapping for actions/labeler

backend/Dockerfile         # Multi-layer Python 3.10 + uv image
backend/.dockerignore      # Docker build exclusions
compose.yml                # Production base (db, adminer, prestart, backend)
compose.override.yml       # Dev overrides (Traefik, live reload, mailcatcher)
compose.traefik.yml        # Production HTTPS (Let's Encrypt ACME)

Makefile                   # Dev shortcuts (up, down, test, lint, migrate, etc.)
.pre-commit-config.yaml    # Hooks: ruff, ty, uv-lock, conventional commits

backend/scripts/
  prestart.sh              # Migrations + initial data + content sync
  test.sh                  # Run pytest
  tests-start.sh           # Run pytest with coverage
  lint.sh                  # ty + ruff checks
  format.sh                # Auto-format with ruff
```

## Dependencies

None — ci is independent infrastructure tooling.

## Testing

- Pre-commit hooks: `pre-commit run --all-files`
- CI workflows: push a branch and verify jobs pass
- Docker: `make up` and verify services start
