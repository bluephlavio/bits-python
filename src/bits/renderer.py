import hashlib
import shutil
import subprocess
from pathlib import Path
from typing import Dict

from .helpers import tmpdir, write


class Renderer:
    _cache: Dict[str, str] = {}

    @staticmethod
    def _generate_hash(tex_code: str) -> str:
        return hashlib.md5(tex_code.encode("utf-8")).hexdigest()

    @staticmethod
    def render(tex_code: str, dest: Path, output_tex: bool = False) -> None:
        current_hash = Renderer._generate_hash(tex_code)
        if dest in Renderer._cache and Renderer._cache[dest] == current_hash:
            print(f"No changes detected for {dest}, skipping rendering Latex.")
            return

        with tmpdir():
            tex_file = Path(f"{dest.stem}.tex")
            write(tex_code, tex_file)

            if output_tex:
                tex_dest = dest.with_suffix(".tex")
                tex_dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(tex_file), str(tex_dest))
                Renderer._cache[dest] = current_hash
                return

            try:
                subprocess.check_call(
                    [
                        "pdflatex",
                        "-interaction=nonstopmode",
                        str(tex_file),
                    ],
                    # stdout=subprocess.DEVNULL,
                    # stderr=subprocess.DEVNULL,
                )
                pdf_file = tex_file.with_suffix(".pdf")
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(pdf_file), str(dest))
                Renderer._cache[dest] = current_hash
            except subprocess.CalledProcessError:
                print("Latex build failed")
