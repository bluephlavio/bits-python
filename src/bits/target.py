import shutil
import subprocess
from multiprocessing import Process
from pathlib import Path
from typing import List

from jinja2 import Template

from .collections import Element
from .models import TargetModel
from .helpers import tmpdir, write


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

    def __str__(self) -> str:
        return f"Target: {self.name or self.id}"

    def __repr__(self) -> str:
        return f"Target(name={self.name}, tags={self.tags}, dest={self.dest}, template={self.template.filename}, context={self.context})"

    def to_model(self) -> TargetModel:
        return TargetModel(
            name=self.name,
            tags=self.tags,
            template=str(self.template_path),
            context=self.context,
            dest=str(self.dest),
        )

    def render(self) -> None:
        def run():
            tex_code: str = self.template.render(**self.context)
            with tmpdir():
                tex_file = Path(f"{self.dest.stem}.tex")
                write(tex_code, tex_file)
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
                except subprocess.CalledProcessError:
                    print("Latex Build failed")

        process: Process = Process(target=run)
        process.start()
        process.join()
