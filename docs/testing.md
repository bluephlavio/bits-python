Purpose

- Summarize test strategy and coverage to guide new contributions.

Overview

- Test structure:
  - Unit tests in `tests/unit/` for parser/dumper, registry, renderer,
    error handling.
  - E2E tests in `tests/e2e/` for CLI smoke (`--version`, `--help`, `build`).
  - Shared fixtures and resources in `tests/conftest.py`, `tests/resources/`.

Key Areas Covered

- Registry parsing/dumping
  - `tests/unit/test_parse_dump.py` validates YAML/MD symmetry.
  - `tests/unit/test_registryfile.py` exercises block resolution API.
  - `tests/unit/test_registry_factory.py` covers directory index lookup and
    factory cache behavior (placeholders for additional cases).

- Rendering
  - `tests/unit/test_renderer.py` verifies render cache and log error parsing
    without requiring a real LaTeX toolchain.

- CLI
  - `tests/e2e/test_cli.py` runs `bits` to check version/help/build.
  - `tests/e2e/test_watch_error_handling.py` validates error types and basic
    watch-mode resilience assumptions (no live watcher in CI).

- Errors and UX
  - `tests/unit/test_error_handling.py` checks rich error formatting,
    suggestions, and chained causes.

Running Tests

```bash
pytest -q
```

Artifacts & Templates

- `.bitsrc` supplies `${artifacts}` and `${templates}` paths for tests.
- Generated files (PDF/TeX) are written under `tests/artifacts/` in tests.

When Adding Tests

- Start narrow (unit tests close to the change), then add e2e if needed.
- Use `tests/resources/` for sample registries and templates.
- Keep deterministic output; avoid relying on external LaTeX unless using
  `--output-tex` to validate TeX-only paths.

