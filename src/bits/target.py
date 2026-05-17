import datetime as _dt
import uuid
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
        # Resolved output specs, populated by RegistryFile after construction.
        # Each entry: {name, template, context, dest (Path|None), suffix, default}
        self._outputs: list[dict] = []

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

    def get_output(self, name: str) -> dict | None:
        for o in self._outputs:
            if o["name"] == name:
                return o
        return None

    def _get_default_output(self) -> dict | None:
        for o in self._outputs:
            if o["default"]:
                return o
        return self._outputs[0] if self._outputs else None

    def _compute_output_dest(self, output: dict) -> Path:
        if output["dest"] is not None:
            d = output["dest"]
            if d.suffix == "":
                stem = self.dest.stem
                if output["suffix"]:
                    return d / f"{stem}-{output['suffix']}.pdf"
                return d / f"{stem}.pdf"
            return d
        base = self.dest
        if output["suffix"]:
            return base.parent / f"{base.stem}-{output['suffix']}{base.suffix}"
        return base

    def _render_one(
        self,
        template: Template,
        context: dict,
        dest: Path,
        do_tex: bool,
        do_pdf: bool,
        *,
        build_dir: Path | None = None,
        intermediates_dir: Path | None = None,
        keep_intermediates: str = "none",
        unique_strategy: str | None = None,
    ) -> None:
        tex_code = template.render(**context)

        final_dest = dest
        if unique_strategy in ("uuid", "timestamped"):
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
        output_name: str | None = None,
        all_outputs: bool = False,
    ) -> None:
        do_pdf = bool(both or (pdf is True and not output_tex))
        do_tex = bool(output_tex or tex or both)

        render_kwargs = dict(
            build_dir=build_dir,
            intermediates_dir=intermediates_dir,
            keep_intermediates=keep_intermediates,
            unique_strategy=unique_strategy,
        )

        if self._outputs:
            if all_outputs:
                for out in self._outputs:
                    self._render_one(
                        out["template"],
                        out["context"],
                        self._compute_output_dest(out),
                        do_tex,
                        do_pdf,
                        **render_kwargs,
                    )
            else:
                if output_name is not None:
                    out = self.get_output(output_name)
                    if out is None:
                        available = [o["name"] for o in self._outputs]
                        raise ValueError(
                            f"Output '{output_name}' not found in target"
                            f" '{self.name}'. Available: {available}"
                        )
                else:
                    out = self._get_default_output()
                self._render_one(
                    out["template"],
                    out["context"],
                    self._compute_output_dest(out),
                    do_tex,
                    do_pdf,
                    **render_kwargs,
                )
        else:
            if output_name is not None:
                raise ValueError(
                    f"Target '{self.name}' has no outputs defined;"
                    " --output requires outputs to be configured"
                )
            self._render_one(
                self.template,
                self.context,
                self.dest,
                do_tex,
                do_pdf,
                **render_kwargs,
            )
