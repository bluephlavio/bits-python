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
            name: Forza peso e massa
          context:
            pick: [1, 2]
---
name:: Forza peso e massa
tags:: [forza-peso, massa, marte, terra, accelerazione-gravità]
defaults::
  items:
  - Calcola la massa del corpo.
  - Calcola l'accelerazione di gravità su Marte.

```latex
Un corpo che sulla Terra pesa \SI{100}{\newton} su Marte pesa \SI{38}{\newton}.
\BLOCK{ set filtered_items = pick|map('getitem', items)|list }
\BLOCK{ if filtered_items|length == 1 }
\VAR{ filtered_items[0] }
\BLOCK{ elif filtered_items|length > 1 }
\begin{enumerate}
\BLOCK{ for item in filtered_items }
\item \VAR{ item }
\BLOCK{ endfor }
\end{enumerate}
\BLOCK{ else }
\BLOCK{ endif }
```