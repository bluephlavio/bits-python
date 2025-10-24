from pathlib import Path
from unittest.mock import patch, MagicMock

from bits.renderer import Renderer


def _setup_fake_pdflatex_call(tmpdir: Path, stem: str):
    # Create fake output files as if pdflatex ran
    (tmpdir / f"{stem}.pdf").write_text("PDF")
    (tmpdir / f"{stem}.aux").write_text("AUX")
    (tmpdir / f"{stem}.log").write_text("LOG")


def test_renderer_keep_intermediates_all(tmp_path: Path):
    tex_code = r"\\documentclass{article}\\begin{document}X\\end{document}"
    dest = tmp_path / "out.pdf"
    build_dir = tmp_path / "_tmp"
    inter_dir = tmp_path / "_build"

    def fake_check_call(cmd, cwd=None):
        _setup_fake_pdflatex_call(Path(cwd), dest.stem)
        return 0

    with patch("subprocess.check_call", side_effect=fake_check_call):
        Renderer.render(
            tex_code,
            dest,
            output_tex=False,
            build_dir=build_dir,
            intermediates_dir=inter_dir,
            keep_intermediates="all",
        )

    assert dest.exists()
    # intermediates copied
    assert (inter_dir / dest.stem / f"{dest.stem}.aux").exists()


def test_renderer_tex_only_writes_tex(tmp_path: Path):
    tex_code = r"\\documentclass{article}\\begin{document}Y\\end{document}"
    dest = tmp_path / "out.pdf"
    Renderer.render(tex_code, dest, output_tex=True)
    assert dest.with_suffix(".tex").exists()
