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

- Standard string-source bits: `\\VAR{ block.render() }`.
- Fragmented bits with a `default` fragment: `\\VAR{ block.render() }`
  renders `src.default`.
- Fragmented bits without `default`: choose a fragment explicitly with
  `\\VAR{ block.render('equation') }`, `\\VAR{ block.render('plot') }`, and so
  on. The core never selects the first mapping entry automatically.
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
  required unless the bit defines a `default` fragment.
- `Block.render(part: str | None, **ctx)` — uses the block context plus
  optional per-call overrides.
- `Block.has_fragment(name)` — checks for a named fragment without reaching
  into `Bit` internals.
- `Block.render_fragment(name, missing=None, **ctx)` — renders a named
  fragment and returns `missing` when it is absent.
- `Block.fragment(name).render(**ctx)` — convenience renderer bound to the
  block, with per-call overrides.

Default Fragment
----------------

`default` is a technical core convention for the fragment used by
`render()` with no argument. It does not mean "student text" or any other
domain-specific role; callers can define fragments such as `solution`, `plot`,
`left`, or `right` according to their own templates.

```yaml
src:
  default: |
    Testo ordinario del bit.
  solution: |
    Soluzione o svolgimento.
```

Notes
-----

- Markdown registries (`.md`) only support single‑string `src` and cannot dump
  multi‑fragment bits.
