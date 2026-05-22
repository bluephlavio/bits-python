# Dialects and Authoring Experiments

## Status

Implemented generic extension point, plus architectural note.

This document describes how experimental authoring dialects plug into
`bits-python` while keeping the core package agnostic and reusable.

Concrete dialects are developed in real workspaces or companion packages, not
inside the core package. `bits-python` only loads and applies named transforms.

---

## Current Usage

A bit can opt into a workspace-defined dialect:

```yaml
bits:
  - name: Example
    dialect: example
    src: '@hello, \VAR{ name }!'
```

Register the dialect in `.bitsrc`, `.bits.toml`, or another loaded config file:

```toml
[dialects]
example = "./plugins/example_dialect.py:transform"
```

The referenced callable receives source text before normal Jinja rendering and
returns source text that the existing render pipeline already understands:

```python
# plugins/example_dialect.py

def transform(source: str, **kwargs) -> str:
    return source.replace("@hello", "Hello")
```

With context `{name: "Ada"}`, the bit above renders as:

```text
Hello, Ada!
```

The configured value format is:

```text
/path/to/module.py:function_name
```

Relative paths follow the same path semantics as existing Jinja plugin files:
they are interpreted by `Path(...)` from the current build process, after config
interpolation has run.

## Transform Contract

The preferred transform signature is:

```python
def transform(
    source: str,
    *,
    context: dict | None = None,
    path: str | None = None,
    metadata: dict | None = None,
) -> str:
    ...
```

`bits-python` currently passes:

* `source`: the selected bit source fragment;
* `context`: the render context available to that bit render call;
* `path`: the registry path when the bit came from a registry file;
* `metadata`: bit metadata such as name, tags, num, kind, level, and dialect.

Simpler callables are also accepted. For example, this works:

```python
def transform(source: str) -> str:
    return source
```

The loader inspects the callable signature and passes only supported keyword
arguments unless the callable accepts `**kwargs`.

## Pipeline

Dialect transforms run only for bit `src`, not target templates:

```text
registry parse
  ↓
model construction
  ↓
source fragment selected for render
  ↓
if dialect is set: workspace transform
  ↓
Jinja render
  ↓
LaTeX/template assembly
  ↓
PDF/TeX outputs
```

For multi-fragment sources, each rendered fragment is transformed
independently:

```yaml
bits:
  - name: Multi
    dialect: example
    src:
      default: "@hello"
      solution: "@hello from the solution"
```

## Errors

Unknown dialects fail clearly:

```text
Unknown dialect 'bits'. Configure it under [dialects] in .bitsrc/.bits.toml.
```

Workspace transforms may raise `bits.exceptions.DialectError` directly:

```python
from bits.exceptions import DialectError

def transform(source: str, **kwargs) -> str:
    raise DialectError(
        "missing @end",
        dialect="example",
        line=12,
        source_path=kwargs.get("path"),
    )
```

Other transform exceptions are wrapped as `DialectError` with the dialect name,
source path when available, and the original exception as the cause.

## Initial Limitations

`bits-python` does not define `@mcq`, `@tf`, `@tasks`, `@plot`, or any other
authoring construct. Those belong to workspaces.

Transforms are cached by dialect name, configured module path, function name,
and module modification time. A fresh build will pick up changed transform
code. Watch mode does not currently add dialect Python files to the watched
dependency set, so saving only the transform file may require touching a
registry file or restarting the build.

The rest of this page records the design rationale behind this boundary.

---

## Context

`bits-python` was born as a generic engine for authoring parameterized
educational content and assembling assessments from reusable bits. In practice,
the package is useful only when connected to a concrete workspace that defines:

* collections of bits;
* targets and assessment registries;
* LaTeX/Jinja templates;
* custom Jinja filters and macros;
* LaTeX support libraries;
* local authoring conventions;
* output templates such as tests, answer keys, and worked solutions.

This means that `bits-python` is not, and should not pretend to be, a
completely abstract content engine. It is an agnostic core designed to serve
concrete authoring environments.

The current architecture already reflects this balance:

* the core provides parsing, models, queries, rendering, preview, output
  management, plugins, and target assembly;
* workspaces define the actual teaching language: templates, filters, macros,
  layout conventions, assessment styles, and reusable content patterns.

As real-world usage evolves, some workspace conventions may prove generally
useful. The core should make it possible to experiment with these conventions
without immediately baking them into `bits-python`.

---

## Problem

Some recurring authoring patterns are currently possible but syntactically
noisy.

Examples include:

* multiple-choice questions;
* true/false blocks;
* selectable task lists;
* association/matching exercises;
* declarative plots;
* standard solution fragments;
* generated answer keys and correction outputs.

Today these are typically expressed through a mix of:

* YAML registry structure;
* Jinja line statements;
* Jinja call-block macros;
* custom filters;
* LaTeX pseudo-commands;
* TeX support libraries.

This is powerful, but it is not always the most readable authoring surface.

For example, a multiple-choice item may require a Jinja call block plus custom
pseudo-commands for correct and wrong options. This is flexible, but the
authoring intent is hidden inside a technical composition of tools.

A future authoring dialect could allow a cleaner source form such as:

```text
@mcq columns=2 shuffle seed="rel-01"
- wrong option
* correct option
- wrong option
- wrong option
@end
```

or:

```text
@tf
V: true statement
F: false statement
@end
```

The key architectural question is where this kind of syntax should live.

---

## Decision

`bits-python` should not implement concrete authoring dialect semantics at this
stage.

In particular, the core should not initially know what `@mcq`, `@tf`,
`@tasks`, `@plot`, or similar constructs mean.

Instead, `bits-python` should provide generic support for **dialects** as source
transforms.

A dialect is a named, workspace-provided transformation that converts an
authored source string into a string that the existing `bits-python` rendering
pipeline can process.

The concrete dialect implementation should live in the workspace where the
authoring patterns are being tested.

The recommended split is:

```text
bits-python
  generic dialect pipeline
  configurable Jinja environment
  minimal error surface
  stable render pipeline

workspace
  experimental dialect implementation
  concrete authoring syntax
  filters/macros/templates/texlibs
  real-world migration and validation

future platform
  mature DSL/parser/editor derived from workspace experiments
```

---

## Goals

The dialect support in `bits-python` should:

1. allow a bit or registry fragment to opt into a named dialect;
2. load dialect transforms from workspace configuration;
3. apply the transform before the normal Jinja rendering stage;
4. preserve full backward compatibility with existing bits;
5. keep the core independent from any particular educational syntax;
6. provide minimal but useful error reporting for transform failures;
7. allow workspaces to experiment with future authoring languages without
   forking the rendering engine.

---

## Non-goals

This feature should not initially:

* define a standard Bits Markup grammar inside `bits-python`;
* implement `@mcq`, `@tf`, `@tasks`, `@plot`, or any other concrete authoring
  block in the core;
* prescribe any workspace-specific output representation, including assessment
  commands, TeX macros, or answer-layout internals;
* replace existing Jinja filters, macros, or LaTeX templates;
* remove the current LaTeX-friendly Jinja syntax;
* force any existing registry to migrate;
* turn `bits-python` into a full compiler or SaaS platform backend;
* solve complete source maps, IDE integration, or rich diagnostics in the first
  iteration.

---

## Proposed User-Facing Shape

A bit may optionally declare a dialect:

```yaml
bits:
  - name: Relativity MCQ
    dialect: bits
    src: |
      Which quantity remains invariant in special relativity?

      @mcq columns=2 shuffle seed="rel-01"
      - Proper time for all observers
      * The speed of light in vacuum
      - Simultaneity of events
      - Relativistic mass
      @end
```

The dialect name is resolved through local configuration.

Example `.bitsrc`:

```toml
[dialects]
bits = "./plugins/bits_markup.py:transform"
```

The referenced function receives the raw source and returns transformed source
compatible with the normal rendering pipeline.

A workspace may also expose the same transform as a Jinja block filter for
early experimentation:

```jinja
%% filter bits
Which quantity remains invariant in special relativity?

@mcq columns=2 shuffle seed="rel-01"
- Proper time for all observers
* The speed of light in vacuum
- Simultaneity of events
- Relativistic mass
@end
%% endfilter
```

This block-filter path is useful before core-level dialect support exists. Once
dialect support exists, the explicit `dialect:` field is preferred for
whole-bit authoring.

---

## Proposed Transform Contract

A dialect transform should be a callable with a stable, minimal interface:

```python
def transform(
    source: str,
    *,
    context: dict | None = None,
    path: str | None = None,
    metadata: dict | None = None,
) -> str:
    ...
```

Where:

* `source` is the raw bit source before normal Jinja rendering;
* `context` may contain known render context when available;
* `path` may contain the registry path or source identifier;
* `metadata` may contain bit-level metadata such as name, tags, or dialect
  options;
* the return value is a transformed source string.

The implementation passes `source`, `context`, `path`, and `metadata` when the
callable accepts them. The signature leaves room for future richer
integrations.

---

## Pipeline Position

The recommended pipeline is:

```text
registry parse
  ↓
model construction
  ↓
if dialect is set: source transform
  ↓
Jinja render
  ↓
LaTeX/template assembly
  ↓
PDF/TeX outputs
```

The dialect transform should happen before Jinja rendering.

This allows dialects to emit ordinary Jinja/LaTeX-compatible source and reuse
the existing template environment, filters, macros, and rendering behavior.

For example, a workspace dialect may transform:

```text
@mcq columns=2
- A
* B
- C
- D
@end
```

into any workspace-defined source that the normal pipeline can render. The core
should not prescribe the target representation. A transform may emit LaTeX,
Jinja calls, workspace macros, structured intermediate markers later consumed by
filters, or any other representation understood by that workspace.

The important contract is only this:

```text
dialect source
  ↓
workspace transform
  ↓
ordinary source accepted by the existing render pipeline
```

Concrete output forms such as assessment-specific LaTeX commands, answer-layout
macros, or legacy compatibility commands belong to the workspace, not to
`bits-python`.

---

## Jinja Environment Configuration

In addition to dialect support, `bits-python` should make the Jinja environment
syntax configurable while preserving the current defaults.

Current default syntax is LaTeX-friendly and should remain the default:

```text
variables:       \VAR{ ... }
blocks:          \BLOCK{ ... }
comments:        \#{ ... }
line statements: %%
line comments:   %#
```

A future configuration section may allow overrides:

```toml
[jinja.syntax]
block_start_string = "\\BLOCK{"
block_end_string = "}"
variable_start_string = "\\VAR{"
variable_end_string = "}"
comment_start_string = "\\#{"
comment_end_string = "}"
line_statement_prefix = "%%"
line_comment_prefix = "%#"
trim_blocks = true
lstrip_blocks = false
```

The defaults must remain exactly compatible with existing content.

This feature is not required for the first dialect experiments, but it supports
broader authoring research and makes `bits-python` a better experimentation
engine.

---

## Error Reporting

A minimal dialect error type should be introduced:

```python
class DialectError(Exception):
    dialect: str | None
    message: str
    line: int | None
    column: int | None
    source_path: str | None
```

A dialect transform may raise this error when it can identify a useful location.

Example error messages:

```text
Bits dialect error in @mcq block at line 12:
expected exactly one correct option, found 0
```

```text
Bits dialect error at line 8:
missing @end for @tf block
```

The first version does not need perfect source maps. Approximate line numbers
are enough to make experimentation usable.

---

## Compatibility

Dialect support must be opt-in.

Existing registries without `dialect:` must behave exactly as before.

Existing Jinja filters, macros, templates, imports, queries, targets, fragments,
presets, and outputs must continue to work unchanged.

A workspace should be able to mix ordinary and dialect-authored bits in the same
collection. The ordinary bit may use whatever authoring conventions that
workspace currently supports; the dialect-authored bit opts into an additional
source transform.

```yaml
bits:
  - name: Ordinary workspace-authored item
    src: |
      This item uses the workspace's existing Jinja, macros, filters,
      LaTeX support, or other authoring conventions.

  - name: Dialect-authored item
    dialect: bits
    src: |
      @mcq columns=2
      - A
      * B
      - C
      - D
      @end
```

---

## Why Not Put the First Dialect Directly in the Core?

Putting concrete syntax such as `@mcq` directly into `bits-python` would provide
stronger standardization and easier onboarding for new users.

However, it would also create several problems:

* the grammar would stabilize too early;
* each syntax experiment would require changes in both the core and the
  workspace;
* the core would become less agnostic;
* workspace-specific conventions might be mistaken for universal semantics;
* future SaaS or app design could be constrained by premature core decisions.

At this stage, the dialect should mature in a real workspace first.

If a dialect becomes stable and broadly useful, it can later be promoted to:

1. a built-in standard dialect in `bits-python`;
2. an official companion package;
3. a workspace template/profile;
4. a future SaaS/app parser.

This decision should be made after real-world usage, not before.

---

## Recommended Workspace Experiment

A concrete workspace may define a dialect named `bits` or `bits_markup`.

Initial scope should be deliberately small:

1. `@mcq` blocks;
2. `@tf` blocks;
3. minimal errors for missing `@end`, no correct answer, or multiple correct
   answers.

Only after validation should the dialect grow to include:

* `@tasks`;
* `@plot`;
* `@matching`;
* `@solution`;
* `@rubric`;
* higher-level composer syntax.

The workspace should keep legacy syntax available during the experiment.

---

## Success Criteria

Dialect support in `bits-python` is successful if:

* existing content builds unchanged;
* a workspace can register a dialect without modifying the core;
* dialect-authored bits can coexist with legacy bits;
* transform errors are readable enough for day-to-day authoring;
* the core remains unaware of concrete dialect semantics;
* future SaaS/app authoring experiments can reuse lessons from real workspace
  usage.

A workspace dialect experiment is successful if:

* real bits become more readable;
* common authoring mistakes are easier to catch;
* answer keys and solutions still work correctly;
* the syntax remains pleasant after repeated use;
* AI-assisted migration and authoring become easier.

---

## Implementation Sketch

Possible `.bitsrc` shape:

```toml
[dialects]
bits = "./plugins/bits_markup.py:transform"
```

Possible bit shape:

```yaml
bits:
  - name: Example
    dialect: bits
    src: |
      @mcq columns=2
      - wrong
      * correct
      - wrong
      - wrong
      @end
```

Possible internal resolution:

```python
transform = dialect_registry.resolve(bit.dialect)
source = transform(
    bit.src,
    context=render_context,
    path=registry_path,
    metadata={"name": bit.name, "tags": bit.tags},
)
rendered = jinja_render(source, context=render_context)
```

The first implementation may be simpler and evolve toward this contract.

---

## Architectural Principle

`bits-python` should remain a small, flexible core that supports serious
authoring workflows without owning every authoring convention.

The core should provide stable extension points.

Workspaces should use those extension points to discover what a good authoring
language actually needs.

Only proven conventions should become core conventions.
