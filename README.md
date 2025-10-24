# bits

[![CI](https://github.com/bluephlavio/bits-python/actions/workflows/ci.yml/badge.svg)](https://github.com/bluephlavio/bits-python/actions/workflows/ci.yml)

# Masterplan for Bits Package

## Introduction

The **bits** package is a Python-based tool designed to assist educators, particularly in STEM fields, in the efficient creation and management of problem sets, tests, and assignments. The package leverages modern templating techniques to enable the generation of dynamic, reusable, and customizable LaTeX documents, supporting teachers in crafting high-quality assessments with minimal effort.

## Core Purpose

The core objective of **bits** is to streamline the process of producing educational content by:
- **Encouraging Reusability**: Define problems (bits) that can be parameterized and reused across multiple assignments.
- **Automating Generation**: Automatically generate diverse problem sets from templates by tweaking context variables.
- **Simplifying Document Assembly**: Assemble tests and assignments (targets) using a collection of bits and additional metadata.
- **Promoting Consistency**: Ensure uniform formatting and quality across all documents.

## Key Features

## CLI Quick Start

- Build: `bits build <path> [--watch] [--output-tex]`
- Convert: `bits convert <src> [--out <path> | --fmt md|yml|yaml]`

New in this repo:
- Preview: `bits preview <spec> [--out DIR] [--pdf|--tex|--both] [--no-plugins]`
  - Spec examples: `file.yml`, `file.yml:"Bit Name"#2:default`, `file.yml[Bit Name#2@1:default]`
- Plugins: declare plugin files in `.bitsrc` under `[jinja]` `plugins = ./filters/custom.py`.
- Output management: `--pdf`, `--tex`, `--both`, plus `--keep-intermediates`, `--intermediates-dir`, `--build-dir`.

See `docs/preview-and-plugins.md` for details and examples.

### 1. **Bits and Targets**
- **Bits**: Individual problem templates written in a custom syntax inspired by Jinja2 and LaTeX. Each bit can generate multiple problems based on variable context.
- **Targets**: Complete tests or assignments assembled from a list of selected bits. Targets also include metadata such as title, instructions, and additional constant data.

### 2. **Dynamic Contextualization**
Each bit can be customized with specific context variables to generate different variations of a problem, enhancing the diversity of exercises for students.

### 3. **Constants and Additional Blocks**
Constants and auxiliary data can be defined within bitsfiles to include physics formulas, mathematical constants, or any relevant information required for a problem set.

### 4. **File Formats**
- **Bitsfiles**: `.md` or `.yml` files that define bits, targets, and constants.
- **Generated Outputs**: LaTeX files ready for compilation into PDFs.

## Architectural Overview

### Technologies and Frameworks

1. **Python**: The core programming language for the package.
2. **Jinja2**: A templating engine adapted for LaTeX syntax to allow dynamic generation of content.
3. **Markdown/YAML**: Used for defining bits and targets in a human-readable format.
4. **LaTeX**: For high-quality typesetting of mathematical and scientific content.
5. **File System Management**: Organized structure for storing and managing bitsfiles and outputs.

### Package Structure
- **bits/engine**: Core engine for parsing and rendering bits and targets.
- **bits/templates**: Custom Jinja2 templates adapted for LaTeX syntax.
- **bits/models**: Definitions of data models (Bits, Targets, Constants).
- **bits/utils**: Utility functions for file handling, rendering, and metadata management.

### Workflow

1. **Define Bits**: Educators create bits with placeholders for context variables.
2. **Assemble Targets**: Combine bits into targets with metadata and specific contexts.
3. **Render to LaTeX**: The engine compiles the targets into LaTeX.
4. **Compile to PDF**: Final output is a ready-to-use PDF document.

## Implementation Details

### Custom Jinja2 Syntax
- Tailored to align closely with LaTeX, ensuring a smooth integration between templating logic and LaTeX typesetting.
- Syntax extensions facilitate seamless embedding of variables and blocks of content.

### Rendering Pipeline
1. **Parse bitsfiles**: Read `.md` or `.yml` files.
2. **Context Injection**: Apply context variables to bits.
3. **Template Rendering**: Render bits into LaTeX format.
4. **Output Assembly**: Compile the rendered content into complete LaTeX documents.

## Crafting Bitsfiles: Advanced Features and Examples

This section demonstrates how to define bits, use external bits dynamically, and assemble them into structured exercises, leveraging Jinja2 for flexibility.

### Core Components

1. **Bits**: Individual exercises defined with LaTeX and templating.
2. **Blocks**: Bits used within targets or parent bits, enriched with specific context and metadata.
3. **Targets**: Complete assignments or tests assembled from blocks.
4. **Constants**: Reusable values across multiple bits or targets.

---

### Examples: Step-by-Step Guide

This section provides examples of bitsfiles and their integration in targets.

#### 1. **Short Markdown Example**

Markdown bitsfiles can define problems as follows:

```markdown
---
tags: [arithmetic]
---
name:: Simple Addition
tags:: [addition]
src:: |
  $5 + 7$.
---
name:: Simple Multiplication
tags:: [multiplication]
src:: |
  $3 \times 4$.
```

---

#### 2. **External Bits File in YAML: `equations.yml`**

This file contains standalone equation bits:

```yaml
tags: [equation]
bits:
  - name: Linear Equation
    num: 1
    tags: [linear]
    src: |
      $x + 3 = 7$
  - name: Quadratic Equation
    tags: [quadratic]
    src: |
      $x^2 - 4x + 3 = 0$
```

---

#### 3. **Parent Bit in YAML: `combined-equations.yml`**

This parent bit references external bits dynamically:

```yaml
bits:
  - name: Equations
    tags: [equations]
    defaults:
      blocks:
        - registry: ./equations.yml
          query:
            tags: [equation]
            picklist: [1, 2]
    src: |
      Solve the following equations.
      \begin{enumerate}
      {% for block in blocks|pick(picklist) %}
          \item {{ block.render() }}
      {% endfor %}
      \end{enumerate}
```

---

### Output Explanation

When rendered, a target using the parent bit produces:

```
Solve the following equations:
\begin{enumerate}
    \item Solve for $x$: $x + 3 = 7$.
    \item Solve for $x$: $x^2 - 4x + 3 = 0$.
\end{enumerate}
```

### Key Features

1. **Dynamic Querying**:
   - The parent bit queries external bits using `tags` and `picklist` to dynamically select and include content.
   
2. **Flexible Composition**:
   - Selected bits are dynamically inserted into an `enumerate` environment, demonstrating Jinja2’s templating power.

3. **Metadata**:
   - Targets add metadata like points to organize and assess problem blocks.

---

### Key Concepts: Context Variables and Defaults

**Context variables** and **defaults** allow bits to dynamically adapt their content based on the target's specific needs or predefined values.

#### **Context Variables**

Context variables are placeholders within a `src` field, which are dynamically replaced with specific values when rendering.

**Example**: A parameterized bit:

```yaml
bits:
  - name: Parameterized Linear Equation
    tags: [equation, linear]
    src: |
      Solve for $x$: ${{ a }}x + {{ b }} = 0$
```

When used in a target:

```yaml
targets:
  - name: parameterized-equation-test
    context:
      blocks:
        - query:
            name: Parameterized Linear Equation
          context:
            a: 2
            b: -6
```

This renders as:

```
Solve for $x$: $2x - 6 = 0$
```

#### **Defaults**

Defaults define fallback values for context variables directly within a bit.

**Example**: A quadratic equation bit:

```yaml
bits:
  - name: Quadratic Equation
    tags: [equation, quadratic]
    defaults:
      a: 1
      b: -3
      c: 2
    src: |
      Solve for $x$: ${{ a }}x^2 + {{ b }}x + {{ c }} = 0$
```

If no context is provided, it renders:

```
Solve for $x$: $x^2 - 3x + 2 = 0$
```

---

## Future Directions

### 1. **Feature Enhancements**
- **Interactive Problem Preview**: A web-based interface to preview problem variations before generating the final document.
- **Advanced Context Management**: Introduce dependencies and dynamic computations between context variables.
- **Template Inheritance**: Allow bits to extend other bits for complex problem hierarchies.

### 2. **Quality of Life Improvements**
- **Error Reporting and Debugging**: Improved error messages for debugging LaTeX rendering and syntax issues.
- **Enhanced Documentation**: More comprehensive user guides and examples.

---

## Conclusion

The **bits** package offers a robust, scalable, and flexible solution for educators to create and manage high-quality STEM assessments. Its modular design and reliance on proven technologies ensure adaptability to future needs, making it a valuable tool in the modern educational landscape.
