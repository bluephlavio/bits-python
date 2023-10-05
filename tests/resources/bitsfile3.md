---
targets:
  - name: target
    template: ./templates/problem-set.tex.j2
    dest: ../artifacts/
    context:
      metadata: true
      title: Title
      subtitle: Subtitle
      blocks:
        - query:
            name: Equazioni
          context:
            blocks:
              - query:
                  tags: [equazione]
                  num: 2
              - query:
                  tags: [equazione]
                  num: 3
---
name:: Equazioni
tags:: [equazioni]
num:: 1

```latex
Risolvi le seguenti equazioni.

\begin{enumerate}
\BLOCK{ for block in blocks }
\item \VAR{ block.render() }
\BLOCK{ endfor }
\end{enumerate}
```
---
tags:: [equazione]
num:: 2

```latex
$x+1=0$
```
---
tags:: [equazione]
num:: 3

```latex
$x^2+1=0$
```