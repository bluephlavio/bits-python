Multi‑fragment Bit Sources
==========================

Overview
--------

- Each Bit may define `src` as either a single string (legacy) or a mapping of
  named fragments. Fragments render independently through the existing
  Jinja→LaTeX→PDF pipeline.
- This feature is fully backward compatible: bits using `src: <string>` are
  unchanged.

Authoring (YAML)
----------------

```yaml
bits:
  - name: Line Match Atom
    defaults: { a: 1, b: 2, c: 3 }
    src:
      equation: "$a + $b = $c"   # plain text or Jinja
      plot: "Plot(\\VAR{ a },\\VAR{ b })"
```

Rendering in Targets
--------------------

- Standard bits: `\\VAR{ block.render() }`.
- Fragmented bits: `\\VAR{ block.render('equation') }`,
  `\\VAR{ block.render('plot') }`.
- A layout that uses all fragments of selected bits might look like:

```latex
% First row: plots
\BLOCK{ for block in blocks }
  \item \VAR{ block.render('plot') }
\BLOCK{ endfor }

% Second row: equations
\BLOCK{ for block in blocks }
  \item \VAR{ block.render('equation') }
\BLOCK{ endfor }
```

API Additions
-------------

- `Bit.is_multi_fragment: bool`
- `Bit.fragment_names: list[str]`
- `Bit.render(part: str | None, **ctx)` — when multi‑fragment, `part` is
  required to avoid ambiguity.
- `Block.render(part: str | None, **ctx)` — uses the block context plus optional per‑call overrides.
- `Block.fragment(name).render(**ctx)` — convenience renderer bound to the block, with per‑call overrides.

Notes
-----

- Markdown registries (`.md`) only support single‑string `src` and cannot dump
  multi‑fragment bits.
