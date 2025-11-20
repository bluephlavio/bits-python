Preview, Plugins, and Output Management

Overview
- Adds a Jinja plugin loader so users can extend filters without touching core.
- Adds a preview command to render bitsfiles or individual bits quickly.
- Adds output management flags to control pdf/tex and LaTeX intermediates.

Jinja Plugin Loader
- Contract: each plugin file must export `register(env)` and mutate the env.
  - Example:
    - def register(env):
      - def double(x): return x * 2
      - env.filters["double"] = double
- Configuration in `.bitsrc` (INI syntax):
  - [jinja]
    plugins      = ./filters/math_filters.py, ./filters/school_filters.py
    filter_files = ./filters/math_auto_filters.py
    macro_files  = ${variables:templates}/macros/association.tex.j2
- CLI option to disable plugins: `--no-plugins` (for both `build` and `preview`).
- Load order: plugins are loaded in the order declared; later definitions override earlier ones.
  - `filter_files` are loaded after `plugins`; all top‑level functions in each
    file (except private names and `register`) become filters.
  - `macro_files` are compiled as Jinja templates in the bits environment; all
    exported macros are registered as globals (callable from any bit/template).

Preview Builds
- Command: `bits preview <spec> [--out DIR] [--pdf|--tex|--both] [--no-plugins]`.
- Spec forms:
  - Whole bitsfile: `path/to/file.yml`
  - Colon: `path/to/file.yml:"Bit Name"#2:preset`
  - Brackets: `path/to/file.yml[Bit Name#2@1:preset]`
    - Supports `#num` disambiguation and optional `@idx` when multiple matches remain.
- Templates:
  - Bitsfile: `src/bits/config/templates/preview.tex.j2`
  - Single bit: `src/bits/config/templates/bit-preview.tex.j2`
  - Both can be overridden in `.bitsrc` under `[preview.templates]`:
    - bitsfile = /abs/path/to/preview.tex.j2
    - bit      = /abs/path/to/bit-preview.tex.j2
- Output naming (readable, stable):
  - Bitsfile: `<bitsfileSlug>.tex` (and `.pdf` if requested)
  - Bit: `<bitsfileSlug>__<bitSlug>__n-<num>__p-<preset>.tex`

Output Management
- Applies to both `build` and `preview`.
- Artifacts: `--pdf`, `--tex`, or `--both` (default preview is tex; default build is pdf).
- Intermediates:
  - `--keep-intermediates` = `none | errors | all`
  - `--intermediates-dir` to collect aux files
  - `--build-dir` working dir for LaTeX runs (fresh per target/preview)
- Behavior:
  - On success and `all`, copies intermediates to `<intermediates_dir>/<stem>/`.
  - On failure and `errors|all`, preserves intermediates and surfaces log path.

Config Basics (.bitsrc)
- INI with extended interpolation for `${var}` placeholders in YAML/MD fixtures.
- Typical entries:
  - [variables]
    artifacts = /abs/path/to/tests/artifacts
    templates = /abs/path/to/tests/resources/templates
  - [jinja]
    plugins = ./filters/math_filters.py
  - [preview]
    out_dir = .bitsout/preview
    pdf = false
    tex = true
  - [preview.templates]
    # Optional, leave blank to use packaged defaults
    ; bitsfile = ${variables:templates}/preview/bitsfile-preview.tex.j2
    ; bit      = ${variables:templates}/preview/bit-preview.tex.j2

Best Practices for Config and Tests
- Package defaults:
  - Keep sane defaults inside the package (already present under `src/bits/config/`).
  - Avoid writing into `~/.bits` at import time when possible. If you need to populate, do it best‑effort (and we already guard for permission errors).
  - Prefer reading packaged defaults via `importlib.resources` or similar; only copy when the user explicitly asks to customize.
- Test hermeticity:
  - Do not rely on a developer’s `~/.bits`. Keep test paths self‑contained.
  - Options (ordered by robustness):
    - Check in a test `.bitsrc` under `tests/` and ensure tests read it (cwd or explicit override).
    - Or inject config in tests programmatically (e.g., set `config.set("variables", "templates", ...)` in `tests/conftest.py`).
    - Or add an environment override (e.g., a `BITS_CONFIG` env var pointing to a config file) — easy follow‑up enhancement.
- Developer UX:
  - Keep `.bitsrc` optional for users. Defaults should let `bits preview` and `bits build` run with template paths embedded in registries.
  - When projects need shared defaults, check in a project `.bitsrc` alongside the registries.

Examples
- Preview a bitsfile (tex only):
  - `bits preview tests/resources/bits-presets.yaml --tex --out tests/artifacts/preview`
- Preview a single bit with preset:
  - `bits preview tests/resources/bits-presets.yaml[Mass of the Sun:default] --tex`
- Build a specific target only:
  - `bits build tests/resources/bits-presets.yaml::t1 --both`
- Keep intermediates on success:
  - `bits build tests/resources/bits-presets.yaml --pdf --keep-intermediates all --intermediates-dir .bitsout/_build --build-dir .bitsout/_tmp`
