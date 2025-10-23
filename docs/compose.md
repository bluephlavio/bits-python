# Compose

- Per named query entry: `compose.<name>`
  - `flatten: true|false` (required when list-of-lists; defaulted to true with a warning for legacy).
  - `merge: concat|interleave` for flattening strategies.
  - `dedupe: by:name|by:id|by:hash` to remove duplicates.
  - `shuffle`, `seed`, `limit` for post-processing.
  - `as`: expose under a different variable name.

- Aggregate compose: `compose.<new>` with `{ from: [var1, var2], flatten, merge, as }`.
