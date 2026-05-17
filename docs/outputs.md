# Target Outputs

## Motivation

A single logical target — with its resolved queries, compose, and context — often needs to
produce more than one artifact. For example, an exam might need a student sheet and a
teacher answer key that draw on the **same** set of bits, in the **same** order, with the
**same** randomisation seed, but rendered through different templates or with extra context.

The naive solution is to define two separate targets that both extend a base target.
`outputs` removes that duplication: one target resolves queries once, then renders
multiple variants from the shared result.

## YAML Schema

```yaml
targets:
  - name: worksheet
    template: ${templates}/student.tex.j2
    dest: ${artifacts}
    context:
      title: Worksheet
    queries:
      blocks:
        - where: { tags: [topic] }
    compose:
      blocks: { flatten: true, as: blocks }

    outputs:
      - name: student          # rendered with the target's own template
        default: true

      - name: teacher
        suffix: teacher        # file becomes: worksheet-teacher.pdf/.tex
        template: ${templates}/teacher.tex.j2
        context:
          render_mode: teacher # merged on top of the resolved target context
```

### `TargetOutputModel` fields

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Identifier for this output variant (required) |
| `template` | `str \| null` | Alternative template path; falls back to the target's template |
| `dest` | `str \| null` | Alternative destination; falls back to the target's dest |
| `suffix` | `str \| null` | Appended to the file stem: `<target>-<suffix>.pdf` |
| `context` | `dict` | Overlay merged on top of the resolved target context |
| `default` | `bool` | Marks the output used by legacy `bits build` (no `--output` flag) |

At most one output may have `default: true`; loading raises an error otherwise.
If no output carries `default: true`, the **first** output is used as the default.

## Naming

| Scenario | Result file |
|---|---|
| `dest: ./dist` (dir), no suffix | `./dist/worksheet.pdf` |
| `dest: ./dist` (dir), `suffix: teacher` | `./dist/worksheet-teacher.pdf` |
| `dest: ./dist/custom.pdf`, `suffix: teacher` | `./dist/custom-teacher.pdf` |
| output has `dest: ./other` (dir) | `./other/worksheet.pdf` |
| output has `dest: ./other/out.pdf` | `./other/out.pdf` |

## Context merge

The `context` field of each output is **deep-merged** on top of the fully-resolved target
context (after queries/compose). Dicts are merged recursively; scalars and lists are
replaced by the output value.

```yaml
# Target resolves to:
context:
  title: Worksheet
  answer_policy:
    seed: 42
    order: shuffle

# Output overlay:
outputs:
  - name: teacher
    context:
      render_mode: teacher

# Effective context for the teacher output:
# title: Worksheet
# answer_policy: { seed: 42, order: shuffle }
# render_mode: teacher
```

## Queries are resolved once

The bits query, compose, picklist, seed, and block ordering are determined by the target
and **shared** across all outputs. Each output only changes what is rendered, not what is
selected.

## CLI

```bash
# Build the default output (or the single artifact if no outputs defined)
bits build registry.yaml --target worksheet --tex

# Build a specific output variant
bits build registry.yaml --target worksheet --output teacher --tex

# Build all output variants in one command
bits build registry.yaml --target worksheet --all-outputs --tex
bits build registry.yaml --target worksheet --all-outputs --pdf
bits build registry.yaml --target worksheet --all-outputs --both
```

Error cases:

- `--output NAME` on a target with no `outputs` → clear error, non-zero exit.
- `--output MISSING` (name not found in outputs) → clear error, non-zero exit.
- `--all-outputs` on a target with no `outputs` → behaves like a normal build (no error).

## Relation to `extends`

`extends` and `outputs` solve different problems:

| | `extends` | `outputs` |
|---|---|---|
| Use case | Logical variant of a target (different topic, profile, course) | Multiple artifacts from the same logical target |
| Query resolution | Each derived target resolves its own queries | Shared — resolved once for the parent target |
| Result | Independent targets queryable by name | Sub-variants of one target, not independently queryable |

Use `extends` when the derived target has different bits, a different query, or
represents a conceptually different document. Use `outputs` when you want the same
document rendered through different templates or with extra context keys.
