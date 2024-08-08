---
targets:
- name: target
  template: ./templates/problem-set.tex.j2
  dest: ${artifacts}
  context:
    metadata: true
    title: Title
    subtitle: Subtitle
    blocks:
    - query:
        name: Equazioni
    - query:
        name: Equazioni
      context:
        blocks:
        - registry: ./collection.md
          query:
            tags: [equazione]
            num: 1
        - registry: ./collection.yml
          query:
            tags: [equazione]
            num: 2
---
name:: Equazioni
tags:: [equazioni]
defaults::
  blocks:
  - registry: ./collection.md
    query:
      tags: [equazione]

```latex
Risolvi le seguenti equazioni.

\BLOCK{ if blocks|length > 0 }
\begin{enumerate}
\BLOCK{ for block in blocks }
\item \VAR{ block.render() }
\BLOCK{ endfor }
\end{enumerate}
\BLOCK{ endif }
```