import shutil
import subprocess
from multiprocessing import Process
from pathlib import Path
from typing import List
import hashlib

from jinja2 import Template

from .collections import Element
from .helpers import tmpdir, write
from .models import TargetModel


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
        def run():
            tex_code: str = self.render_tex_code()
            current_hash = hashlib.md5(tex_code.encode('utf-8')).hexdigest()

            if current_hash == self._last_rendered_hash:
                print("No changes detected, skipping rendering Latex.")
                return

            with tmpdir():
                tex_file = Path(f"{self.dest.stem}.tex")
                write(tex_code, tex_file)

                if output_tex:
                    tex_dest = self.dest.with_suffix(".tex")
                    tex_dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(tex_file), str(tex_dest))
                    self._last_rendered_hash = current_hash
                    return

                try:
                    subprocess.check_call(
                        [
                            "pdflatex",
                            "-interaction=nonstopmode",
                            str(tex_file),
                        ]
                    )
                    pdf_file = tex_file.with_suffix(".pdf")
                    self.dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(pdf_file), str(self.dest))
                    self._last_rendered_hash = current_hash
                except subprocess.CalledProcessError:
                    print("Latex build failed")

        process: Process = Process(target=run)
        process.start()
        process.join()
