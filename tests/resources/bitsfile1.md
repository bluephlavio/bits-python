---
targets:
  - name: target
    template: ${templates}/problem-set.tex.j2
    dest: ../artifacts/
    context:
      metadata: true
      fontsize: 13pt
      title: Title
      subtitle: Subtitle
      blocks:
        - query:
            name: Mass of the Sun
---
name:: Mass of the Sun
tags:: [astronomy, gravitation]
author:: Flavio Grandin
defaults:: { formula: "M=\\frac{Fr^2}{Gm}" }

```latex
Calculate the mass of the Sun with the formula $\VAR{ formula }$!!!
```