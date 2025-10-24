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
    def render(
        tex_code: str,
        dest: Path,
        output_tex: bool = False,
        *,
        build_dir: Optional[Path] = None,
        intermediates_dir: Optional[Path] = None,
        keep_intermediates: str = "none",
    ) -> None:
        current_hash = Renderer._generate_hash(tex_code)
        if dest in Renderer._cache and Renderer._cache[dest] == current_hash:
            print(f"No changes detected for {dest}, skipping rendering Latex.")
            return

        # Prepare working directory
        def _copy_intermediates(src_dir: Path, dest_root: Path):
            if dest_root is None:
                return
            outdir = dest_root / dest.stem
            outdir.mkdir(parents=True, exist_ok=True)
            for item in src_dir.iterdir():
                try:
                    if item.is_file():
                        shutil.copy(str(item), str(outdir / item.name))
                except Exception:
                    pass

        if build_dir is not None:
            work_dir = Path(build_dir) / dest.stem
            # fresh per render attempt
            if work_dir.exists():
                shutil.rmtree(work_dir, ignore_errors=True)
            work_dir.mkdir(parents=True, exist_ok=True)
            cwd_ctx = None
        else:
            cwd_ctx = tmpdir()

        try:
            if cwd_ctx is not None:
                wd_path = Path(cwd_ctx.__enter__())
            else:
                wd_path = work_dir

            tex_file = wd_path / f"{dest.stem}.tex"
            write(tex_code, tex_file)

            if output_tex:
                tex_dest = dest.with_suffix(".tex")
                tex_dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(str(tex_file), str(tex_dest))
                # Do NOT update cache on tex-only output; we may still need to build PDF next.
                return

            log_file = tex_file.with_suffix(".log")
            try:
                # Ensure TeX can write cache files in the working directory on first run
                env = os.environ.copy()
                env.setdefault("TEXMFVAR", str(wd_path))
                subprocess.check_call(
                    [
                        "pdflatex",
                        "-interaction=nonstopmode",
                        str(tex_file.name),
                    ],
                    cwd=str(wd_path),
                    env=env,
                )
                pdf_file = wd_path / f"{dest.stem}.pdf"
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(str(pdf_file), str(dest))
                Renderer._cache[dest] = current_hash

                if keep_intermediates == "all" and intermediates_dir is not None:
                    _copy_intermediates(wd_path, Path(intermediates_dir))
            except subprocess.CalledProcessError as e:
                error_detail = Renderer._extract_error_from_log(log_file)
                preserved_log = None
                if log_file.exists():
                    preserved_log = dest.parent / f"{dest.stem}_latex_error.log"
                    preserved_log.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(str(log_file), str(preserved_log))

                if (
                    keep_intermediates in ("errors", "all")
                    and intermediates_dir is not None
                ):
                    _copy_intermediates(wd_path, Path(intermediates_dir))

                raise LatexRenderError(
                    message="LaTeX compilation failed",
                    detail=error_detail or f"Process returned code {e.returncode}",
                    log_file=str(preserved_log) if preserved_log else None,
                ) from e
        finally:
            if cwd_ctx is not None:
                try:
                    cwd_ctx.__exit__(None, None, None)
                except Exception:
                    pass

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
