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
        - query:
            tags: [equazione]
            num: 1
    - query:
        name: Equazioni
      context:
        blocks:
        - query:
            tags: [equazione]
            num: 3
---
name: Equazione
tags:: [equazione]
num:: 1

```latex
$x+1=0$
```
---
name: Equazione
tags:: [equazione]
num:: 2

```latex
$x^2+1=0$
```
---
name:: Equazioni
tags:: [equazioni]
defaults::
  blocks:
  - query:
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
---
name: Equazione
tags:: [equazione]
num:: 3

```latex
$x^3+1=0$
```