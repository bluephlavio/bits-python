import importlib.metadata
from typer.testing import CliRunner
from pathlib import Path
import os
import shutil
import pytest
import subprocess
import tempfile

from bits.cli.main import app
from bits.config import config


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    version = importlib.metadata.version("bits")
    assert result.output.strip() == f"bits {version}"


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"], prog_name="bits")
    assert result.exit_code == 0
    help_output = result.output
    assert "Usage: bits [OPTIONS] COMMAND [ARGS]..." in help_output


def test_cli_build(bitsfiles):
    runner = CliRunner()
    for bitsfile in bitsfiles:
        result = runner.invoke(app, ["build", str(bitsfile), "--tex"], prog_name="bits")
        assert result.exit_code == 0


def test_cli_build_single_target(bitsfiles):
    # Pick a known file with target 't1'
    runner = CliRunner()
    for bitsfile in bitsfiles:
        if bitsfile.name == "bits-presets.yaml":
            target_spec = f"{bitsfile}::t1"
            result = runner.invoke(
                app, ["build", target_spec, "--tex"], prog_name="bits"
            )
            assert result.exit_code == 0
            break


def test_cli_build_pdf_minimal(resources):
    # Skip if pdflatex is unavailable or cannot compile a trivial document
    def _can_compile():
        if shutil.which("pdflatex") is None:
            return False
        with tempfile.TemporaryDirectory() as td:
            tex = Path(td) / "t.tex"
            tex.write_text("\\documentclass{article}\\begin{document}x\\end{document}")
            env = os.environ.copy()
            # Ensure TeX caches/logs go to a writable location; some setups need this
            env.setdefault("TEXMFVAR", td)
            proc = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex.name],
                cwd=td,
                capture_output=True,
                env=env,
            )
            return proc.returncode == 0 and (Path(td) / "t.pdf").exists()

    if not _can_compile():
        pytest.skip("pdflatex not functional in environment")
    runner = CliRunner()
    path = resources / "minimal-pdf.yaml"
    result = runner.invoke(app, ["build", str(path), "--pdf"], prog_name="bits")
    assert result.exit_code == 0
    # Expected output PDF in artifacts
    artifacts_dir = Path(config.get("variables", "artifacts"))
    expected_pdf = artifacts_dir / "minimal.pdf"
    if not expected_pdf.exists():
        # In local envs without full TeX deps, be lenient; CI asserts strictly
        if os.environ.get("CI"):
            print("CLI output:\n", result.output)
            print("Looked for:", expected_pdf)
            print("Artifacts dir contents:", list(artifacts_dir.glob("*.pdf")))
            assert expected_pdf.exists()
        else:
            pytest.skip("PDF not generated in local env")


def test_cli_build_pdf_presets(resources):
    # Skip if pdflatex is unavailable or cannot compile a trivial document
    def _can_compile():
        if shutil.which("pdflatex") is None:
            return False
        with tempfile.TemporaryDirectory() as td:
            tex = Path(td) / "t.tex"
            tex.write_text("\\documentclass{article}\\begin{document}x\\end{document}")
            env = os.environ.copy()
            env.setdefault("TEXMFVAR", td)
            proc = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex.name],
                cwd=td,
                capture_output=True,
                env=env,
            )
            return proc.returncode == 0 and (Path(td) / "t.pdf").exists()

    if not _can_compile():
        pytest.skip("pdflatex not functional in environment")

    runner = CliRunner()
    path = resources / "bits-presets.yaml"
    result = runner.invoke(app, ["build", str(path), "--pdf"], prog_name="bits")
    assert result.exit_code == 0
    artifacts_dir = Path(config.get("variables", "artifacts"))
    expected_pdf = artifacts_dir / "t1.pdf"
    if not expected_pdf.exists():
        if os.environ.get("CI"):
            print("CLI output:\n", result.output)
            print("Looked for:", expected_pdf)
            print("Artifacts dir contents:", list(artifacts_dir.glob("*.pdf")))
            assert expected_pdf.exists()
        else:
            pytest.skip("PDF not generated in local env")
