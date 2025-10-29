Purpose

- Summarize core modules and end-to-end data flow for bits-python.

Module Map

- Registry
  - `src/bits/registry/registry.py` — abstract `Registry`, holds bits,
    constants, targets, deps, and watch API.
  - `src/bits/registry/registryfile.py` — file-backed registry (YAML/MD),
    parsing, imports, resolution of targets/blocks/constants.
  - `src/bits/registry/registryfile_parsers.py` — YAML/Markdown parsers.
  - `src/bits/registry/registryfile_dumpers.py` — YAML/Markdown dumpers.
  - `src/bits/registry/registry_factory.py` — path normalization, directory
    index detection, caching, and creation of registries.

- Models (pydantic)
  - `src/bits/models/bit_model.py`, `target_model.py`, `constant_model.py`.
  - `src/bits/models/blocks_model.py`, `bits_query_model.py`,
    `constants_model.py`, `constants_query_model.py`.
  - `src/bits/models/registry_model.py` — aggregate `RegistryDataModel`.

- Domain entities
  - `src/bits/bit.py` — a renderable unit (source + defaults + metadata).
  - `src/bits/block.py` — bit + context + metadata for composition.
  - `src/bits/target.py` — output document rendered to `.pdf` or `.tex`.
  - `src/bits/constant.py` — named symbol/value for tables.
  - `src/bits/collections/` — generic typed collections with query/filter.

- Rendering & templating
  - `src/bits/env.py` — Jinja2 environment. LaTeX-friendly delimiters:
    `\BLOCK{...}` and `\VAR{...}`; registers filters.
  - Plugins (declared in `.bitsrc`) — provide filters like `pick`, `render`, `enumerate`, `show`, `ceil`,
    `floor`, `getitem`.
  - `src/bits/renderer.py` — TeX generation, LaTeX compile (`pdflatex`),
    content-hash cache, error extraction.

- CLI and UX
  - `src/bits/cli/main.py` — Typer app: `build`, `convert`, `--version`.
  - `src/bits/cli/helpers.py` — error panels, suggestions, watch loop.

- Config & YAML
  - `src/bits/config.py` — merges `~/.bits/config.ini` with local `.bitsrc`.
  - `src/bits/yaml_loader.py` — `${var}` interpolation via config.
  - Defaults and templates under `src/bits/config/` (copied to `~/.bits`).
  - Utilities: `src/bits/helpers.py` (IO utils, path normalization, tmpdir).

Data Flow

1) Input registry (YAML or Markdown)
   - File discovered via `RegistryFactory.get(path)`.
   - If directory, looks for `index.md`, `index.yaml`, `index.yml`.

2) Parse → models
   - YAML: `RegistryFileYamlParser` loads frontmatter-like structure.
   - Markdown: `RegistryFileMdParser` reads file-level frontmatter and per-bit
     fenced blocks (```latex ... ```), with `::` normalized to `:` in headers.
   - Parsed into `RegistryDataModel` and nested models.

3) Models → runtime objects
   - Bits: `BitModel` → `Bit` (Jinja template compiled via `EnvironmentFactory`).
   - Constants: `ConstantModel` → `Constant`.
   - Targets: `TargetModel` resolved into `Target` with template lookup.

4) Target resolution and queries
   - Targets carry:
     - `context`: static variables only (titles, class, date, options).
     - `queries`: dynamic inputs (named queries like `blocks`, `constants`).
     - `compose`: how to assemble list-of-lists and expose final names.
   - Named queries support:
     - `registry` (optional): resolve from another registry file.
     - `where`: regex fields (`name`, `tags`, `num`, `author`, `kind`, `level`) plus `has`/`missing`.
     - `select`: `{ indices (1-based), k|limit, offset, shuffle, sample, seed }`.
     - `preset`: bit preset selector (id or 1-based index; numeric strings try id then index).
     - `with`: structured overlay: `{ context: {...}, queries: {...} }`.
   - Compose (per named or aggregate): `{ flatten, merge: concat|interleave, dedupe: by:name|by:id|by:hash, shuffle, seed, limit, as }`.
   - Legacy `context.blocks`/`context.constants` are mapped to `queries` with a deprecation warning and default compose (`flatten: true`, `as: blocks|constants`).

5) Render
   - `Target.render_tex_code()` renders Jinja with LaTeX delimiters.
   - `Renderer.render(tex, dest, output_tex)` writes `.tex` or compiles via
     `pdflatex`, moving the `.pdf` to `dest`.

6) Caching & watch
   - Renderer cache: content-hash per `dest` to skip unchanged compilations.
   - Env cache: Jinja environment per template folder in `EnvironmentFactory`.
   - Watch: `Watcher` + `Registry.add_listener/watch/stop` used by CLI.

CLI Entry Points

- `bits build <path> [--watch] [--output-tex]`
  - Creates registry, renders targets, optionally watches files.

- `bits convert <src> [--out <path> | --fmt md|yml|yaml]`
  - Loads registry and dumps to requested format.

Error Handling

- Exception types under `src/bits/exceptions.py` categorize failures
  (registry, template, LaTeX, filesystem, config, build).
- CLI formats detailed panels with suggestions and cause chains.

Dependencies & External Tools

- `pdflatex` required for PDF generation (use `--output-tex` to skip).
- `watchdog` used for file watching.
