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

    def render(
        self,
        output_tex: bool = False,
        *,
        pdf: bool | None = None,
        tex: bool | None = None,
        both: bool = False,
        build_dir: Path | None = None,
        intermediates_dir: Path | None = None,
        keep_intermediates: str = "none",
        unique_strategy: str | None = None,
    ) -> None:
        tex_code: str = self.render_tex_code()
        # Determine modes
        do_pdf = bool(both or (pdf is True and not output_tex))
        do_tex = bool(output_tex or tex or both)

        # Compute final destination (supports unique naming)
        final_dest = self.dest
        if unique_strategy in ("uuid", "timestamped"):
            import uuid
            import datetime as _dt

            stem = final_dest.stem
            if unique_strategy == "uuid":
                suffix = uuid.uuid4().hex[:8]
            else:
                suffix = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
            new_name = f"{stem}__{suffix}{final_dest.suffix}"
            final_dest = final_dest.with_name(new_name)

        if do_tex:
            Renderer.render(tex_code, final_dest, True)
        if do_pdf:
            Renderer.render(
                tex_code,
                final_dest,
                False,
                build_dir=build_dir,
                intermediates_dir=intermediates_dir,
                keep_intermediates=keep_intermediates,
            )
