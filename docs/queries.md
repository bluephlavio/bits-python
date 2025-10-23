# Queries DSL

- Named queries live under `targets[].queries`.
- Supported names: `blocks`, `constants`.
- Fields per sub-query:
  - `registry`: path to another registry to query (optional).
  - `where`: filter fields (`id_`, `name`, `tags`, `num`, `author`, `kind`, `level`) with regex matching; supports `has` and `missing` lists.
  - `select`: `{ indices (1-based), k|limit, offset, shuffle, sample, seed }`.
  - `preset`: pick a bit preset by id or by 1-based index (numeric strings try id first, then index).
  - `with`: structured overlay applied to every returned bit:
    - `context`: shallow variables (merged deeply across maps).
    - `queries`: inline named queries resolved and exposed alongside.

Notes

- `has`/`missing` for constants recognizes `name`, `symbol`, `value`.
- If a named query is a list of sub-queries, compose controls flatten/merge.
- Legacy `context.blocks/constants` are supported with a deprecation warning.
