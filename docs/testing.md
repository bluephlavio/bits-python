# Testing Guide

Layout

- Unit tests under `tests/unit/` grouped by feature:
  - parsing/dumping, queries+compose, where/select, presets, with validation, constants filters, etc.
- E2E tests under `tests/e2e/` run the `bits` CLI over all valid registries.
- Fixtures under `tests/resources/`:
  - Valid registries at the top level.
  - Invalid fixtures under `tests/resources/invalid/` (excluded from e2e).
  - Templates under `tests/resources/templates/`.

Conventions

- Keep fixtures minimal; prefer single-purpose YAML files per case.
- Reuse existing templates to avoid duplication and stabilize outputs.
- Assert deterministically: set `seed` where randomness is used.
- For legacy mapping assertions, use `warnings` capture where needed.
