---
targets:
  - name: target
    template: ./templates/test.tex.j2
    dest: ../artifacts/
    context:
      title: Title
      subtitle: Subtitle
      class_: Class
      type: null
      date: Date
      blocks:
        - registry: ./collection.md
          query:
            name: Mass of the Sun
          metadata:
            pts: [25, 25, 25, 25]
---