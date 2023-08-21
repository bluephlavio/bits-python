---
targets:
  - name: target1
    template: ./templates/base.tex.j2
    dest: ../artifacts/
    context:
      title: Title
      subtitle: Subtitle
      class_: Class
      type: null
      date: Date
      blocks:
        - registry: ./bitsfile1.md
          query:
            name: Mass of the Sun
          metadata:
            pts: [25, 25, 25, 25]
---