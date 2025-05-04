import hashlib
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional

from .exceptions import LatexRenderError
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

        with tmpdir() as temp_dir:
            tex_file = Path(f"{dest.stem}.tex")
            write(tex_code, tex_file)

            if output_tex:
                tex_dest = dest.with_suffix(".tex")
                tex_dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(tex_file), str(tex_dest))
                Renderer._cache[dest] = current_hash
                return

            log_file = tex_file.with_suffix(".log")
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
            except subprocess.CalledProcessError as e:
                # Extract error details from the log file if it exists
                error_detail = Renderer._extract_error_from_log(log_file)

                # Create a copy of the log file for reference
                preserved_log = None
                if log_file.exists():
                    preserved_log = dest.parent / f"{dest.stem}_latex_error.log"
                    preserved_log.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(str(log_file), str(preserved_log))

                # Raise a specific exception with the LaTeX error details
                raise LatexRenderError(
                    message="LaTeX compilation failed",
                    detail=error_detail or f"Process returned code {e.returncode}",
                    log_file=str(preserved_log) if preserved_log else None,
                ) from e

    @staticmethod
    def _extract_error_from_log(log_file: Path) -> Optional[str]:
        """
        Extract the most relevant error message from a LaTeX log file.

        Args:
            log_file: Path to the LaTeX log file

        Returns:
            A string containing the extracted error message or None if no error was found
        """
        if not log_file.exists():
            return None

        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                log_content = f.read()

            # Common LaTeX error patterns to search for
            error_patterns = [
                # Look for lines containing "! LaTeX Error:"
                r"! LaTeX Error: ([^\n\r]*)",
                # Look for lines containing "! Package error:"
                r"! Package [^\n\r]* Error: ([^\n\r]*)",
                # Look for any other error
                r"! ([^\n\r]*)",
            ]

            # Try to find the first matching error pattern
            import re

            for pattern in error_patterns:
                matches = re.search(pattern, log_content)
                if matches and matches.group(1):
                    return matches.group(1).strip()

            return None
        except Exception:
            # If anything goes wrong while parsing the log, just return None
            return None
