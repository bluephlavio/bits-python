Purpose

- Define key abstractions with brief examples for quick orientation.

Core Abstractions

- Bit (`src/bits/bit.py`)
  - A single renderable item (exercise, snippet) written in LaTeX-flavored
    Jinja. Has metadata (`name`, `tags`, `author`, `level`, `kind`),
    `defaults` for context, and `src` for the template.
  - Renders via `bit.render(**context)`.

- Block (`src/bits/block.py`)
  - Wraps a Bit with per-use `context` and `metadata`. Used inside targets
    to render selected bits.

- Target (`src/bits/target.py`)
  - A full document using a LaTeX Jinja template (`template`), a `context`
    (often includes a list of blocks and constants), and an output `dest`.
  - `render(output_tex=False)` renders PDF (or `.tex` if `output_tex=True`).

- Registry (`src/bits/registry/`)
  - A container of bits, constants, and targets sourced from a YAML/Markdown
    file. `RegistryFile` resolves imports and builds runtime objects.

- Constants (`src/bits/constant.py`)
  - Named values to print in tables (e.g., physics constants). Selected via
    queries and made available in target context.

Queries

- Across collections, `query()` supports filters from models:
  - Bits: `id_`, `name`, `tags`, `num`, `author`, `kind`, `level`.
  - Constants: `id_`, `name`, `tags`.
- Queries populate `blocks` or `constants` within context.

Context & Defaults

- `defaults` on a Bit are merged with invocation time context at render.
- Context keys `blocks` and `constants` are expanded by the registry loader:
  - `blocks`: a list of `BlocksModel` entries (see YAML) that may specify a
    `registry:` to query remote bits.
  - `constants`: a list of `ConstantsModel` entries.

Templates & Filters

- Jinja delimiters are LaTeX friendly:
  - Blocks: `\BLOCK{ ... }`
  - Vars: `\VAR{ ... }`
- Built-in filters (`src/bits/filters.py`):
  - `pick(items, picklist, start=1)` — select positions.
  - `enumerate(items, opts="")` — produce a LaTeX enumerate.
  - `render(item)` — render a `Block` or return the item.
  - `show(items, single_item_template, preamble, opts)` — single vs list view.
  - `ceil`, `floor`, `getitem` — simple utilities.

YAML/Markdown Registries

- YAML (example):

```yaml
tags: [sample]
imports:
  - registry: ./collection.yml
bits:
  - name: Linear Equation
    tags: [equation]
    defaults: { a: 1, b: -3 }
    src: |
      Solve: $\VAR{a}x + \VAR{b} = 0$.
targets:
  - name: sheet
    template: ${templates}/problem-set.tex.j2
    dest: ${artifacts}
    context:
      title: Title
      blocks:
        - query: { tags: [equation] }
```

- Markdown (example):

```markdown
---
targets:
  - name: sheet
    template: ${templates}/test.tex.j2
    dest: ${artifacts}
---
name:: Linear Equation
tags:: [equation]
defaults:: { a: 1, b: -3 }

```latex
Solve: $\VAR{a}x + \VAR{b} = 0$.
```
```

Variable Interpolation

- `${var}` in YAML/MD is resolved from config (`.bitsrc`, `~/.bits/config.ini`).
  See `src/bits/yaml_loader.py` and `src/bits/config.py`.

Watch Mode

- `bits build --watch` watches the registry and imported files and triggers
  re-renders. Errors are shown but the loop continues until fixed.

Caching

- Renderer caches a content hash per destination path to skip unchanged runs.
- EnvironmentFactory caches Jinja environments per template folder.

Error Reporting

- Structured exceptions in `src/bits/exceptions.py` and pretty output in
  `src/bits/cli/helpers.py` with categories, suggestions, and cause chains.

