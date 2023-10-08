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
        - registry: ./bitsfile3.md
          query:
            name: Equazioni
          context:
            blocks:
              - registry: ./bitsfile3.md
                query:
                  tags: [equazione]
                  num: 2
              - registry: ./bitsfile3.md
                query:
                  tags: [equazione]
                  num: 3
---