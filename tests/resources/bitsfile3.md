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
---
name:: Equazioni
tags:: [equazioni]
author:: Flavio Grandin

```latex
Risolvi le seguenti equazioni.

\begin{enumerate}
\BLOCK{ for block in blocks }
\item \VAR{ block.render() }
\BLOCK{ endfor }
\end{enumerate}
```
---
name:: Equazione
tags:: [equazione]
author:: Flavio Grandin

```latex
$x+1=0$
```
---
name:: Equazione
tags:: [equazione]
author:: Flavio Grandin

```latex
$x^2+1=0$
```