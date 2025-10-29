bits-python — Agent Guide

Purpose

- Give AI agents and developers a concise map of this repo, how to reason
  about it, and how to extend it safely.

Quick Repo Map

- Core package: `src/bits`
  - `bit.py` — Bit entity (templated item) and rendering.
  - `block.py` — Wrapper for a Bit with per-use context/metadata.
  - `target.py` — Full document to render (template + context + dest).
  - `renderer.py` — LaTeX/TeX rendering, caching, PDF writing.
  - `env.py` — Jinja2 environment with LaTeX-friendly delimiters + filters.
  - `registry/` — Registry abstraction and `RegistryFile` (YAML/Markdown),
    parse/dump factories, watch integration.
  - `models/` — Pydantic models for registries, bits, targets, constants.
  - `cli/` — Typer CLI (`bits`) with commands `build` and `convert`, plus
    error UI and watch loop helpers.
  - `config.py` — Config resolution and defaults (`~/.bits`, `.bitsrc`).
  - `yaml_loader.py` — YAML loader with `${var}` interpolation.
  - `exceptions.py` — Typed error classes and categories.

Answering Questions (for agents)

- Prefer citing code locations with file paths (e.g., `src/bits/bit.py:1`).
- Explain concepts via the canonical entities:
  - Bit, Block, Target, Registry, Constants.
  - Queries (name/tags/num/etc.), Context/Defaults, Templates, Filters.
- For data flow, reference: registry parsers → models → objects → target
  resolution → Jinja render → `renderer.py` → PDF/TeX.
- For CLI behavior, reference: `src/bits/cli/main.py`, `src/bits/cli/helpers.py`.
- For config and vars (e.g., `${templates}`), reference: `src/bits/config.py`,
  `src/bits/yaml_loader.py`, and `~/.bits/config.ini`, `.bitsrc`.

Safe Modification Guidelines

- Keep module boundaries:
  - Rendering logic in `renderer.py` only.
  - Templating surface via `env.py` filters; register new filters there.
  - Registry parsing/dumping in `registry/` factories and classes.
  - Data shapes in `models/` (use pydantic models consistently).
- Respect parsing/dumping round-trips (see tests). If you add fields, update
  both parser and dumper and their models.
- Maintain CLI stability; add options in a backwards-compatible way unless an
  RFC approves breaking changes.
- Preserve watch mode resilience; never crash the watch loop on recoverable
  errors (use error helpers and typed exceptions).
- Use the typed exceptions in `exceptions.py` for new error surfaces.

Documentation Workflow

- Update or add pages in `docs/` when changing architecture, concepts,
  filters, CLI options, or templates.
- Keep examples runnable with local `tests/resources` where possible.
- Keep lines ≤80 chars and prefer short examples.

Feature Proposal Template (RFC)

- Title
- Problem
- Proposed Changes
  - Modules touched and rationale
  - Data model impacts (pydantic updates)
  - CLI/API changes (flags, commands, entries)
  - Templates/filters additions
- Alternatives Considered
- Migration/Compatibility
- Testing Plan (unit/e2e, resources)
- Observability/Errors (which exception types, user guidance)

How to Extend

- New template: place `.tex.j2` under your templates folder; point a target’s
  `template:` to it or set a default in `.bitsrc`/`~/.bits/config.ini`.
- New query field: update the relevant pydantic model in `src/bits/models/`
  and honor it in `collections.Collection.query()` consumers.
- New registry format: add a parser/dumper and plug it into
  `RegistryFileParserFactory`/`RegistryFileDumperFactory`.

Local Execution & Tests

- Build: `bits build <path> [--watch] [--output-tex]`.
- Convert: `bits convert <src> [--out <path> | --fmt md|yml|yaml]`.
- Tests: `pytest` (uses `tests/resources` and writes to `tests/artifacts`).
- LaTeX: PDF generation requires `pdflatex` on PATH; use `--output-tex` to
  skip PDF.

Conventions

- Jinja delimiters for LaTeX: `\BLOCK{ ... }`, `\VAR{ ... }`.
- YAML interpolation: `${var}` from `.bitsrc` `[variables]` (and `~/.bits`).
- Registries: YAML or Markdown with front matter; may `import` other
  registries.

Checklist Before Merging

- Code: types, boundaries, factories updated.
- Docs: `docs/` pages and examples updated.
- Tests: updated/added and passing locally.
- CLI: help text and examples verified.

