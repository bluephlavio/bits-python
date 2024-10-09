from pathlib import Path
from typing import List

from jinja2 import Template

from .collections import Element
from .models import TargetModel
from .renderer import Renderer


class Target(Element):
    def __init__(  # pylint: disable=too-many-arguments
        self,
        template: Template,
        context: dict,
        dest: Path,
        name: str | None = None,
        tags: List[str] | None = None,
    ):
        super().__init__(name=name, tags=tags)

        self.template: Template = template
        self.template_path = Path(template.filename).resolve()

        self.context: dict = context

        if dest.suffix == "":
            self.dest: Path = dest / f"{self.name or self.id}.pdf"
        elif dest.suffix == ".pdf":
            self.dest: Path = dest
        else:
            raise ValueError("Target destination must be a pdf file")

        self._last_rendered_hash = None

    def __str__(self) -> str:
        return f"Target: {self.name or self.id}"

    def __repr__(self) -> str:
        return "".join(
            [
                "Target(",
                f"name={self.name}, ",
                f"tags={self.tags}, ",
                f"dest={self.dest}, ",
                f"template={self.template.filename}, ",
                f"context={self.context}",
                ")",
            ]
        )

    def to_model(self) -> TargetModel:
        return TargetModel(
            name=self.name,
            tags=self.tags,
            template=str(self.template_path),
            context=self.context,
            dest=str(self.dest),
        )

    def render_tex_code(self) -> str:
        tex_code: str = self.template.render(**self.context)
        return tex_code

    def render(self, output_tex: bool = False) -> None:
        tex_code: str = self.render_tex_code()
        Renderer.render(tex_code, self.dest, output_tex)
