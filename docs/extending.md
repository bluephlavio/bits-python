Purpose

- Explain how to add filters, templates, or models safely.

Add a New Filter

- Implement function in `src/bits/filters.py`.
- Register it in `EnvironmentFactory.get()` in `src/bits/env.py`:

```python
env.filters["myfilter"] = myfilter
```

- Use it in templates:

```latex
\VAR{ items|myfilter }
```

- Add tests demonstrating behavior and edge cases.
- Document usage in `docs/concepts.md` with an example.

Add a New Template

- Place `.tex.j2` templates in a folder and reference via a target’s
  `template:` field, or configure defaults:
  - Global: `~/.bits/config.ini` (`DEFAULT.template`).
  - Local override: `.bitsrc` (`[DEFAULT] template = ...`).

- Example target:

```yaml
targets:
  - name: sheet
    template: ${templates}/problem-set.tex.j2
    dest: ${artifacts}
```

Extend Models or Queries

- Update/add pydantic models under `src/bits/models/`.
- Ensure `collections.Collection.query()` consumers account for new fields.
- Update both parser and dumper if registry surface changes.
  - Parsers: `src/bits/registry/registryfile_parsers.py`.
  - Dumpers: `src/bits/registry/registryfile_dumpers.py`.
- Add tests for parse→dump roundtrips (`tests/unit/test_parse_dump.py`).

Extend the CLI

- Add commands in `src/bits/cli/main.py` and utilities in
  `src/bits/cli/helpers.py`.
- Keep non-TTY output stable (avoid ANSI when output is captured).
- Provide examples in `docs/cli.md` and tests in `tests/e2e/`.

Add a New Registry Format

- Implement a parser and dumper, then register both in factories:
  - `RegistryFileParserFactory.get(path)`
  - `RegistryFileDumperFactory.get(path)`

Errors & Observability

- Use typed errors from `src/bits/exceptions.py`.
- Integrate with the CLI error renderer for actionable suggestions.

Testing Checklist

- Unit tests for new code paths.
- Roundtrip tests for parser/dumper.
- E2E smoke where applicable (build, convert).

