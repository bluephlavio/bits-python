# GUIDE — DESIGNING **BITS** & **TARGETS**: TAXONOMY, ARCHITECTURE, AND BEST PRACTICES

This guide is for authors who build exercise collections (bits) and assessments
(targets). It is not an API manual; it’s a practical, architectural guide to
decide what goes where and why, so your material stays reusable, readable, and
easy to adapt (accommodations, make‑ups, A/B versions).

In three lines:

* Put the data and choices in YAML (bits, constants, targets, queries).
* Put presentation in Jinja templates and LaTeX macros.
* Combine with queries/compose; enable reuse with presets/extends.

---

## 1) Bits taxonomy (decide what you are designing)

From real‑world usage, these types recur. Choosing the right type avoids
duplication and fragility.

### 1.1 Atomic (a.k.a. fragment)

What: a single reusable learning fragment that doesn’t stand alone (plot,
equation, expression, tiny T/F item…).
Where: dedicated “atomic” registries (see §2).
Typical use: rarely used directly by targets; usually assembled by a
composer/aggregator.
Pros: maximum reuse. Cons: requires good naming/tagging.

### 1.2 Standard

What: complete, non‑composing exercise (body + fixed or no list), with moderate
Jinja parameters and no `queries`.
Where: “standard” registries for the subject.
Pros: ready for assessments. Cons: less flexible than a composer.

### 1.3 Context‑Picklist (questions on a fixed context)

When: a single context (e.g., a line with parameter k, a plot, a short text)
plus 3–5 questions that make sense only with that context.
Where: near the standards or in a dedicated file.
How: questions are LaTeX in `src`; pick via `picklist` under `context`/`presets`.

Example (syntax compatible with legacy collections)

```yml
bits:
- name: Line with parameter k — questions
  defaults:
    context: { m: 1, q: -1, picklist: [1,2,3] }
  presets:
    - name: default
      context: { }
    - name: three_questions
      context: { picklist: [1,3,5] }
  src: |
    % The environment reads `pick=` as a comma-separated index string
    \begin{pickitems}[pick=\VAR{ picklist|join(',') }]
      \pickitem{Find k so that the line passes through A(2,3).}
      \pickitem{Find k so that the line is parallel to y = 2x + 1.}
      \pickitem{Find k where it intersects the x‑axis at x = 4.}
      \pickitem{Determine whether there is k such that it is perpendicular to y = -\tfrac{1}{2}x.}
      \pickitem{Find k so that the line is increasing and passes through B(-1,0).}
    \end{pickitems}
```

> Note: `\pickitem{…}` with curly braces is currently required; the environment
> option `pick=` accepts comma‑separated indices (generated here with
> `join(',')`).

### 1.4 Composer (a.k.a. section/collector)

What: bits that aggregate atomics (or standards) via named queries; the target
flattens with `compose`.
Where: subject‑level “composers”.
Pros: reuse and controlled variability. Cons: requires discipline in atomic
registries.

Example

```yml
bits:
- name: Graphs section
  defaults:
    context: {}
    queries:
      blocks:
        - registry: ${collections}/matematica/grafici/atomic.yml
          where: { tags: [retta] }
          select: { k: 2, shuffle: true, seed: 42 }
        - registry: ${collections}/matematica/grafici/atomic.yml
          where: { tags: [parabola] }
          select: { k: 1 }
  src: |
    % Query results are exposed as top‑level vars (no Q.*): use `blocks`
    \BLOCK{ for b in blocks }\VAR{ b.render() }\BLOCK{ endfor }
```

### 1.5 Composer + Picklist

What: the context (e.g., a selected atomic plot) comes from a query; then you
emit a picklist of questions about that context.
Where: among the subject’s composers.

```yml
bits:
- name: Questions on selected plot
  defaults:
    context: { picklist: [1,2,4] }
    queries:
      blocks:
        - registry: ${collections}/matematica/grafici/atomic.yml
          where: { tags: [retta] }
          select: { k: 1 }
  src: |
    \BLOCK{ set p = blocks[0] }\VAR{ p.render() }
    \begin{pickitems}[pick=\VAR{ picklist|join(',') }]
      \pickitem{State the domain.}
      \pickitem{State the positivity set.}
      \pickitem{Symmetries.}
      \pickitem{Intersections with the axes.}
    \end{pickitems}
```

### 1.6 Aggregator — True/False

What: stable wrapper (fixed instructions/layout) that selects n T/F items from
one or more sources.
Where: as a reusable composer (see §2 for placement).
Guideline: if only the source changes, reuse a single parametric aggregator; if
the instructions/layout change, create one variant per subject (put common
pieces in LaTeX macros).

### 1.7 Aggregator — Multiple Choice

What: like T/F but with options and an answer key; randomization/layout managed
by LaTeX macros.
Where: same as above.

### 1.8 Aggregator — Sets (equations/expressions)

What: generates a set of cardinality n, with per‑item points/metadata.
Where: the subject’s aggregator or “shared” if reused elsewhere.

> Duplicate or reuse a composer?
> Reuse when only the source changes (`registry/where/select/with`).
> Duplicate per subject when instructions/layout change (factor common parts
> into LaTeX macros).

What is a preset (clearly, once and for all)
A preset is a curated version of a bit that stores a set of `context` and/or
`queries` values that we know work and want to reuse easily (e.g., `default`,
`short`, `steep`). Presets do not duplicate the bit: a partial override of
`defaults` (maps deep‑merge, lists replace) with optional `overrides.path` for
micro‑patches.

---

## 2) How to organize the repo (folders and boundaries)

Think in stable macro‑areas, with simple names. Two reasonable options for the
“technical” folders.

```
# Option A (minimal and clear)
collections/       # all collections (bits + constants)
assessments/       # targets
templates/         # .tex.j2
texlib/            # LaTeX macros/packages (e.g., BitPlot)
plugins/           # Jinja plugins (filters/tests/globals)

# Option B (plugins explicit)
collections/
assessments/
templates/
texlib/
jinja_plugins/     # instead of plugins/
```

### 2.1 Inside `collections/`: split by semantics + role

* Organize first by subject area (semantics): `grafici/`, `equazioni/`,
  `espressioni/`, `meccanica/`, …
* Inside each area, split by role: `atomic.yml`, `standard.yml`,
  `composers.yml`.
* Stable aggregators (T/F, Multiple Choice, Sets) can:
  * live in the same file as composers if few;
  * move to dedicated files (`truefalse.yml`, `multiplechoice.yml`, `sets.yml`)
    if many/reusable.
* If atomics are numerous, consider an `items/` or `atomic/` subfolder and an
  `index.yml` that exports only curated composers/aggregators.

> Navigation trade‑off: more files/folders = cleaner boundaries but more
> clicks. Avoid monoliths, but don’t over‑fragment.

### 2.2 `index.yml`: the public export

* Exposes only bits with standalone meaning (standards + polished composers).
* Keeps atomics/items “private”.
* Two styles: include+where (automatic) or manifest (manual). See examples §1.

### 2.3 `assessments/` (targets) and its dialogue with collections

* Targets read from `collections/` via `queries` and lay out with the chosen
  `template`.
* Use `extends` to specialize: a base target (class, subject, year) + profiles
  (accommodations/recovery), including multi‑extends and cross‑file (left→right,
  last‑wins).
* Scoring/metadata: keep them near the blocks in `queries.blocks[].metadata`
  (composers stay neutral; targets decide weights).

### 2.4 `templates/`, `texlib/`, `plugins/`

* `templates/`: define presentation (sections, headers, layout). No heavy logic.
* `texlib/`: LaTeX macros/environments (e.g., BitPlot, future mechanics
  modules). All graphics live here.
* `plugins/` (or `jinja_plugins/`): Python with `register(env)` for pure
  filters/tests/globals (no I/O). Declared in `.bitsrc`.

---

## 3) Choose the right layer (quick criteria)

* Quantities/values/choices → YAML (context/presets, queries/select/with).
* Layout → Jinja templates (sections, separators, grids).
* Graphics → LaTeX macros (lines, plots, diagrams).
* Reuse → presets (bits) and extends (targets).
  Clear separation avoids: templates with too many `if`s; bits with copied TikZ;
  YAML trying to do layout.

---

## 4) Key tools (use thoughtfully)

* Presets (bits): curated versions of `defaults`. Maps deep‑merge; lists
  replace; `overrides.path` for micro‑patches.
* `with` (in sub‑queries): set the same parameter for all results; for
  per‑item differences, split into multiple sub‑queries.
* Compose: set `flatten: true` when you get list‑of‑lists; `merge:
  concat|interleave` controls ordering.
* Extends (targets): single/multi inheritance including cross‑file; left→right,
  last‑wins; then apply derived overrides.
* Jinja plugins: local filters (`register(env)`), loaded via `.bitsrc`.

---

## 5) Focused examples

### 5.1 Context‑Picklist with consistent syntax

```yml
bits:
- name: Line with parameter k — questions
  defaults:
    context: { m: 1, q: -1 }
  presets:
    - name: three_questions
      context: { picklist: [1,3,5] }
  src: |
    \begin{pickitems}[pick=\VAR{ picklist|join(',') }]
      \pickitem{Find k so that the line passes through A(2,3).}
      \pickitem{Find k so that the line is parallel to y = 2x + 1.}
      \pickitem{Find k where it intersects the x‑axis at x = 4.}
      \pickitem{Determine whether there is k such that it is perpendicular to y = -\tfrac{1}{2}x.}
      \pickitem{Find k so that the line is increasing and passes through B(-1,0).}
    \end{pickitems}
```

### 5.2 Composer pulling atomics + compose in the target

```yml
bits:
- name: Graphs section
  defaults:
    context: {}
    queries:
      blocks:
        - registry: ${collections}/matematica/grafici/atomic.yml
          where: { tags: [retta] }
          select: { k: 2, shuffle: true, seed: 42 }
        - registry: ${collections}/matematica/grafici/atomic.yml
          where: { tags: [parabola] }
          select: { k: 1 }
  src: |
    % Use top‑level `blocks` and render each block
    \BLOCK{ for b in blocks }\VAR{ b.render() }\BLOCK{ endfor }
```

```yml
# target
compose:
  blocks: { flatten: true, merge: concat, as: blocks }
```

### 5.3 Reusable True/False aggregator (parametric source)

```yml
bits:
- name: True/False — functions
  defaults:
    context: { title: "True or False" }
    queries:
      blocks:
        - registry: ${collections}/matematica/funzioni/atomic.yml
          where: { tags: [monotonia] }
          select: { k: 4, shuffle: true, seed: 11 }
  src: |
    \section*{\VAR{ title }}
    \begin{enumerate}
      \BLOCK{ for b in blocks }\item \VAR{ b.render() }\BLOCK{ endfor }
    \end{enumerate}
```

### 5.4 Set of equations with per‑item points

```yml
bits:
- name: Set of 4 equations
  defaults:
    context: {}
    queries:
      blocks:
        - registry: ${collections}/matematica/equazioni/atomic.yml
          where: { tags: [grado2] }
          select: { k: 4, shuffle: true, seed: 5 }
  src: |
    \begin{enumerate}
      \BLOCK{ for b in blocks }\item (\VAR{ loop.index }\,pt)\; \VAR{ b.render() }\BLOCK{ endfor }
    \end{enumerate}
```

### 5.5 Base target + profiles via extends (multi/cross‑file)

```yml
targets:
- name: Test — Limits (base)
  template: ${templates}/test.tex.j2
  dest: ./dist
  context: { title: "Limits", class_: 5C LSU, date: 10 December 2024 }
  queries:
    blocks:
      - registry: ${collections}/matematica/limiti
        where: { name: "Dal grafico" }
        metadata: { pts: [4,0,0,0] }
      - registry: ${collections}/matematica/limiti
        where: { name: "Calcolo di limiti" }
        metadata: { pts: [5,5,5,0] }
  compose: { blocks: { flatten: true, as: blocks } }

- name: Accommodation profile
  context: { title_suffix: " — BES" }
  queries:
    blocks:
      - metadata: { pts: [3,0,0,0] }
      - metadata: { pts: [4,4,4,0] }

- name: Test — Limits — BES
  extends: ["Test — Limits (base)", "Accommodation profile", "../shared/profili.yml::Header A4"]
  context: { title: "Limits${title_suffix}" }
```

---

## 6) Migrating from legacy (painlessly)

* Move `context.blocks/constants` to `queries.blocks/constants` and add
  `compose.blocks.flatten: true, as: blocks`.
* Turn `query:` into `where:`, and make `compose` explicit.
* Replace duplicated targets (accommodations/recovery/variants) with multi/
  cross‑file extends.
* Add presets for highly parametric bits (a `default` preset is injected by the
  tool; add additional named variants as needed).
* Introduce `index.yml` as the public facade (exclude atomics/items).

---

## 7) Anti‑patterns & trade‑offs

* Splitting questions into atomics when they make sense only within a fixed
  context → use Context‑Picklist.
* Identical composers across folders when only the source changes → reuse a
  single parametric composer (`where/select/with`).
* LaTeX macros inside bits → move to `texlib/`, create reusable environments.
* 200+ bits in one file → unmanageable: split by subject/sub‑topic.
* `with` with free variables → always `{ context: {...}, queries: {...} }`.

---

## 8) What you gain by following these principles

* Less duplication, more coherence.
* Faster updates (presets/extends).
* Cleaner templates (Jinja organizes, LaTeX draws).
* Robust materials for different classes, accommodations, and A/B versions.

When in doubt about “where does this go?”, use the rule of thumb:
parameters/variants → YAML · layout → template · graphics → macros · reuse →
extends · public export → `index.yml`.

