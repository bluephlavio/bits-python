Merge Policy and Override Ops
=============================

This document explains how to replace or deep‑merge whole `context` and
`queries` blocks in both Targets (with `extends`) and Bit presets, and how to
use explicit override operations to patch nested data with deep‑merge.

Key points
- Defaults preserved unless you opt‑in to `replace`.
- Policies apply uniformly to Targets and Bit presets.
- Overrides now support `op: merge|replace|set|clear|remove`.

Per‑node merge policy (Targets and Presets)
- Add a `merge` map with keys `context` and/or `queries`:

  merge:
    context: deep|replace   # default: deep
    queries: deep|replace   # default: deep

- Targets with `extends`:
  - `merge.queries: replace` replaces base queries entirely.
  - `merge.context: replace` replaces base context entirely.
- Bit presets:
  - `merge.queries: replace` ignores default queries from the bit.
  - `merge.context: replace` is accepted for consistency (preset layer only).

Overrides with explicit ops
- Syntax (Targets: queries/context/compose; Presets: queries):

  overrides:
    - path: "queries.blocks[2].where"   # or "context.title", or root: "queries"
      op: merge|replace|set|clear|remove
      value: { name: Q3 }                # if applicable

- Semantics:
  - merge: deep‑merge using the same rules as extends merge
    (dicts recursive; lists index‑wise; scalars replace).
  - replace/set: replace targeted node or list item.
  - clear: set node to empty ({} or []), list item to None.
  - remove: remove key or list item (unchanged).

Examples
1) Target replaces entire queries:

  - name: Derived
    extends: ["Base"]
    merge: { queries: replace }
    queries:
      blocks:
        - where: { name: Q3 }
    compose:
      blocks: { flatten: true, as: blocks }

2) Preset replaces entire context:

  presets:
    - name: ripido
      merge: { context: replace }
      context: { m: 1.2, q: -2 }

3) Override deep‑merge into a list entry:

  overrides:
    - path: "queries.blocks[2]"
      op: merge
      value:
        where: { name: Q3 }
        metadata: { pts: [9, 9] }

4) Root‑level override on queries:

  overrides:
    - path: "queries"
      op: replace
      value:
        blocks:
          - where: { name: Q4 }

Notes
- `compose.merge` continues to control result aggregation; it is unrelated to
  configuration merge policy.
- If you specify invalid policy values or override `op`, a clear error is
  raised during registry load.

