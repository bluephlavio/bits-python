---
targets:
  - name: target
    template: ./template.tex.j2
    dest: ../artifacts/
    context:
      title: Title
      class_: Class
      date: Date
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