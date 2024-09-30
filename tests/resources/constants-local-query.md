---
constants:
- name: Costante di gravitazione universale
  tags: [gravitazione]
  symbol: $G$
  value: $\SI{6.67e-11}{\cubic\meter\per\kilogram\per\squared\second}$
targets:
- name: target
  template: ${templates}/problem-set.tex.j2
  dest: ${artifacts}
  context:
    metadata: true
    fontsize: 13pt
    title: Title
    subtitle: Subtitle
    blocks:
    - query:
        name: Mass of the Sun
    constants:
    - query:
        name: Costante di gravitazione universale
---
name:: Mass of the Sun
tags:: [astronomy, gravitation]
author:: Flavio Grandin
defaults:: { formula: "M=\\frac{Fr^2}{Gm}" }

```latex
Calculate the mass of the Sun with the formula $\VAR{ formula }$!!!
```