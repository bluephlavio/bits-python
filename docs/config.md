Purpose

- Explain how bits reads configuration, what files it looks at, and how to use
  `.bitsrc` / `config.toml` to control paths, plugins, and defaults.

Config Files and Precedence

- bits merges configuration from several sources into a single global
  `config` object (`src/bits/config.py:1`):
  - Global directory: `~/.bits/`
    - `config.ini`
    - `config.toml`
  - Environment override:
    - `BITS_CONFIG=/abs/path/to/config.ini|.toml`
  - Project-local files (highest precedence):
    - `.bits.toml`
    - `.bitsrc`

- Load order and precedence:
  - Global `config.ini` (if present)
  - Global `config.toml` (overrides values from the INI)
  - Env override file from `BITS_CONFIG` (overrides global values)
  - Local `.bits.toml` (overrides previous values)
  - Local `.bitsrc` (overrides everything else)

- Files are merged section by section. Later files can:
  - Add new sections and keys.
  - Override existing keys (last write wins).

Interpolation and Variables

- bits uses `ConfigParser` with `ExtendedInterpolation`, so `${var}` syntax in
  YAML/Markdown is resolved from the merged config (`src/bits/config.py:55`,
  `src/bits/yaml_loader.py`):
  - `${name}` looks in the `DEFAULT` section first, then in named sections.
  - `${section:key}` explicitly references a section/key.

- Common pattern in `.bitsrc`:

```ini
[variables]
artifacts = ./dist
templates = ./templates
```

Then in YAML/MD registries:

```yaml
targets:
  - name: sheet
    template: ${templates}/problem-set.tex.j2
    dest: ${artifacts}
```

This makes paths configurable without changing registries.

INI vs TOML

- Global and local configs can be INI (`.ini`, `.bitsrc`) or TOML
  (`config.toml`, `.bits.toml`).
- TOML handling:
  - bits loads TOML files into nested dicts, then flattens them into INI-like
    sections and keys (`src/bits/config.py:24`).
  - Nested tables become dotted sections. Example:

```toml
[variables]
templates = "tests/resources/templates"

[preview]
pdf = false
tex = true
```

becomes:

- Section `variables` with key `templates`.
- Section `preview` with keys `pdf`, `tex`.

Jinja Configuration

- Jinja is configured via the `[jinja]` section (`src/bits/env.py:19`):

```ini
[jinja]
plugins      = ./filters/math_filters.py, ./filters/school_filters.py
filter_files = ./filters/simple_filters.py
macro_files  = ${variables:templates}/macros/association.tex.j2
```

- `plugins`:
  - List of Python files that export `register(env)` and mutate the Jinja
    environment explicitly.
  - Used for advanced setup (filters, tests, globals).
  - Loaded in order; later plugins may override earlier filters.

- `filter_files`:
  - List of Python files where bits auto-registers filters.
  - For each file:
    - imports the module;
    - registers every top-level callable whose name:
      - does not start with `_`, and
      - is not `register`.
  - Example:

```python
# simple_filters.py
def double(x):
    return x * 2

def add(a, b):
    return a + b
```

becomes:

```jinja
\VAR{ 3|double }          % -> 6
\VAR{ add(2, 5) }         % -> 7
```

- `macro_files`:
  - List of Jinja templates containing macros, compiled into the bits Jinja
    environment and exposed as globals.
  - Example macro file:

```jinja
% macros/association.tex.j2
\BLOCK{ macro render_association(items, seed=None, left2right=False) }
  ... layout using items ...
\BLOCK{ endmacro }
```

With:

```ini
[jinja]
macro_files = ${variables:templates}/macros/association.tex.j2
```

You can call the macro from any bit/src or template:

```jinja
\BLOCK{ render_association(blocks, seed=42, left2right=true) }
```

- CLI flag `--no-plugins`:
  - Disables all plugin and config-driven Jinja customization:
    - `plugins`, `filter_files`, `macro_files` are ignored.
  - Useful for debugging or running in environments without project filters.

Preview and Build Defaults

- Sections `[preview]`, `[preview.templates]`, and `[output]` control CLI
  defaults for `bits preview` and `bits build`. See
  `tests/resources/.bitsrc:1` for a reference.

- Typical `.bitsrc` snippet used in tests:

```ini
[variables]
artifacts = tests/artifacts
templates = tests/resources/templates

[jinja]
plugins = ${variables:templates}/../plugins/default_filters.py

[preview]
out_dir = tests/artifacts/preview
pdf = false
tex = true
naming = readable

[preview.templates]
; bitsfile = ${templates}/preview/bitsfile-preview.tex.j2
; bit      = ${templates}/preview/bit-preview.tex.j2

[output]
pdf = true
tex = false
keep_intermediates = none
intermediates_dir  = .bitsout/_build
build_dir          = .bitsout/_tmp
```

- Behavior:
  - `preview.out_dir`, `preview.pdf`, `preview.tex`, `preview.naming` provide
    defaults for `bits preview` (CLI flags still override).
  - `[preview.templates]` lets you override the built-in preview LaTeX
    templates (`src/bits/config/templates/preview.tex.j2` and
    `bit-preview.tex.j2`).
  - `[output]` provides defaults for `bits build`:
    - whether to emit pdf/tex by default;
    - how to manage LaTeX intermediates.

Global Defaults under `~/.bits`

- On first import, bits copies packaged defaults from `src/bits/config/` to
  `~/.bits` best-effort (`src/bits/config.py:15`):
  - `~/.bits/config.ini` / `config.toml` (if present) can carry user-level
    defaults (paths, Jinja settings, CLI defaults).
  - `~/.bits/templates` may hold user-wide templates.

- This is optional and best-effort:
  - If the home directory is not writable (CI, containers), bits skips copying
    and relies on project-local `.bitsrc` / `.bits.toml` instead.

Practical Recipes

- Project-local setup for a repo:

```ini
; .bitsrc at the project root
[variables]
artifacts = ./dist
templates = ./templates

[jinja]
filter_files = ./filters/filters.py
macro_files  = ${variables:templates}/macros/association.tex.j2

[output]
pdf = true
tex = false
```

This gives:

- `${artifacts}` / `${templates}` available in YAML/MD.
- All functions in `filters/filters.py` auto-registered as Jinja filters.
- `render_association(...)` and other macros from `association.tex.j2`
  available to bits and templates.

- Per-user defaults:
  - Put shared defaults in `~/.bits/config.toml` or `config.ini`:

```toml
[variables]
templates = "/Users/me/bit-templates"

[jinja]
plugins = "/Users/me/bits-filters/math.py"
```

Then use a small `.bitsrc` in each project only for project-specific paths
and overrides.

