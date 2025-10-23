Purpose

- Describe the Typer CLI, commands, options, and usage patterns.

Commands

- Version
  - `bits --version`
  - Prints `bits <version>` using package metadata.
  - Source: `src/bits/cli/main.py:version_callback`.

- Help
  - `bits --help`

- Build
  - `bits build <path> [--watch] [--output-tex]`
  - Resolves `<path>` to a registry (file, or directory with index file) and
    renders all targets.
  - `--watch`: keeps watching for changes and re-renders on edits.
  - `--output-tex`: writes `.tex` files instead of compiling PDFs.
  - Sources: `src/bits/cli/main.py`, `src/bits/cli/helpers.py`.

- Convert
  - `bits convert <src> [--out <path> | --fmt md|yml|yaml]`
  - Loads a registry file and writes it out in the requested format.
  - If `--out` not provided, `--fmt` determines extension.
  - Source: `src/bits/cli/main.py` → `RegistryFactory.get` → `RegistryFile.dump`.

Examples

Render a YAML registry to PDFs in `${artifacts}` and include constants:

```bash
bits build tests/resources/local-query-yaml.yaml
```

Render only TeX files (skip PDF; works without `pdflatex`):

```bash
bits build tests/resources/local-query-yaml.yaml --output-tex
```

Watch and re-render on edits:

```bash
bits build tests/resources/local-query-yaml.yaml --watch
```

Convert between formats:

```bash
bits convert tests/resources/collection.yml --fmt md
bits convert tests/resources/collection.md --out /tmp/out.yml
```

Destinations

- A target’s `dest` may be a directory or a `.pdf` path. If directory, the
  final filename is `<registry-stem>-<target.name>.pdf`.

Error Output

- Failures are prettified by `src/bits/cli/helpers.py` with categories,
  suggestions, and cause chains. Non-bits exceptions include a traceback.

Environment

- Unicode/TTY detection disables rich styling in non-TTY contexts to keep
  CI/log output clean and stable.

