# Defaults and Presets

- Bits have `defaults` as a base (supports `context` and `queries`).
- `presets` are partial overrides applied on top of defaults when selected by a sub-query:
  - `id` is optional; selection accepts id or 1-based index (numeric strings try id then index).
  - `context`: deep-merged maps (preset keys win).
  - `queries`: deep-merge for maps; lists replace entirely. Resolved and exposed alongside context.
  - `overrides`: path-based patches applied to the `queries` object before resolution. Errors on missing paths.

Merge Precedence (per bit)

1. defaults
2. selected preset (context + queries resolved)
3. sub-query `with.context` and `with.queries`
