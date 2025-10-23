Migration Notes: targets.queries and compose

- New: `targets[].queries` holds dynamic selections (e.g., `blocks`, `constants`).
- New: `targets[].compose` controls flattening/merging and variable naming.
- Legacy: `targets[].context.blocks` / `context.constants` are deprecated; they are
  automatically mapped to `queries.blocks` / `queries.constants` with a warning.
  A default compose is applied: `flatten: true`, `as: blocks|constants`.

Examples

- Before (legacy):

  context:
    blocks:
    - query: { name: "Mass of the Sun" }

- After (preferred):

  queries:
    blocks:
      - query: { name: "Mass of the Sun" }
  compose:
    blocks: { flatten: true, merge: concat, as: blocks }

Notes

- Markdown registries (`.md`) remain supported alongside YAML.
- Current implementation supports `flatten`, `merge: concat|interleave`, and `as`.
  Further options (dedupe/shuffle/limit/seed) and `where`/`select` are planned.
