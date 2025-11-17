from pathlib import Path

from typer.testing import CliRunner
from bits.config import config

from bits.cli.main import app
from bits.renderer import Renderer


def test_preview_bitsfile_tex_output(resources):
    runner = CliRunner()
    bitsfile = resources / "bits-presets.yaml"
    outdir = Path("tests/artifacts/preview")
    res = runner.invoke(
        app, ["preview", str(bitsfile), "--tex", "--out", str(outdir)], prog_name="bits"
    )
    assert res.exit_code == 0
    # Expect readable naming: <bitsfileSlug>.tex
    expected = outdir / f"{bitsfile.stem}.tex"
    if not expected.exists():
        print("Preview CLI output:\n", res.output)
        print("out dir:", outdir)
        print(
            "config.preview.out_dir:", config.get("preview", "out_dir", fallback=None)
        )
        print("list out dir:", list(outdir.glob("*")))
    assert expected.exists()


def test_preview_single_bit_with_preset_tex_output(resources):
    runner = CliRunner()
    bitsfile = resources / "bits-presets.yaml"
    outdir = Path("tests/artifacts/preview")
    spec = f"{bitsfile}[Mass of the Sun:default]"
    res = runner.invoke(
        app, ["preview", spec, "--tex", "--out", str(outdir)], prog_name="bits"
    )
    assert res.exit_code == 0
    expected_name = f"{bitsfile.stem}__mass-of-the-sun__p-default.tex"
    expected = outdir / expected_name
    if not expected.exists():
        print("Preview CLI output:\n", res.output)
        print("out dir:", outdir)
        print("list out dir:", list(outdir.glob("*")))
    assert expected.exists()


def test_preview_bitsfile_uses_config_out_dir(resources):
    # No --out flag: should use config [preview].out_dir
    runner = CliRunner()
    bitsfile = resources / "bits-presets.yaml"
    res = runner.invoke(app, ["preview", str(bitsfile), "--tex"], prog_name="bits")
    assert res.exit_code == 0
    out_dir = Path(config.get("preview", "out_dir", fallback=".bitsout/preview"))
    expected = out_dir / f"{bitsfile.stem}.tex"
    if not expected.exists():
        print("Preview CLI output (config out_dir):\n", res.output)
        print("out dir:", out_dir)
        print("list out dir:", list(out_dir.glob("*")))
    assert expected.exists()


def test_preview_single_bit_colon_syntax(resources):
    # Spec: file:"Name":preset (optional #num and @idx supported too)
    runner = CliRunner()
    bitsfile = resources / "bits-presets.yaml"
    outdir = Path(config.get("preview", "out_dir", fallback="tests/artifacts/preview"))
    spec = f"{bitsfile}:\"Mass of the Sun\":default"
    res = runner.invoke(app, ["preview", spec, "--tex"], prog_name="bits")
    assert res.exit_code == 0
    expected_name = f"{bitsfile.stem}__mass-of-the-sun__p-default.tex"
    expected = outdir / expected_name
    if not expected.exists():
        print("Preview CLI output (colon syntax):\n", res.output)
        print("out dir:", outdir)
        print("list out dir:", list(outdir.glob("*")))
    assert expected.exists()


def test_preview_bitsfile_pdf_output(resources, monkeypatch):
    runner = CliRunner()
    bitsfile = resources / "bits-presets.yaml"

    # Stub the LaTeX renderer to avoid pdflatex dependency and to assert path
    calls = {}

    def _fake_render(tex_code, dest, output_tex=False, **kwargs):  # noqa: ARG001
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"%PDF-1.4\n% stub\n")
        calls["dest"] = dest

    monkeypatch.setattr(Renderer, "render", staticmethod(_fake_render))

    res = runner.invoke(app, ["preview", str(bitsfile), "--pdf"], prog_name="bits")
    assert res.exit_code == 0

    out_dir = Path(config.get("preview", "out_dir", fallback=".bitsout/preview"))
    expected_pdf = out_dir / f"{bitsfile.stem}.pdf"
    if not expected_pdf.exists():
        print("Preview CLI output (pdf):\n", res.output)
        print("out dir:", out_dir)
        print("list out dir:", list(out_dir.glob("*")))
    assert expected_pdf.exists()
    assert calls.get("dest") == expected_pdf


def test_preview_single_bit_with_preset_pdf_output(resources, monkeypatch):
    runner = CliRunner()
    bitsfile = resources / "bits-presets.yaml"
    spec = f"{bitsfile}[Mass of the Sun:default]"

    calls = {}

    def _fake_render(tex_code, dest, output_tex=False, **kwargs):  # noqa: ARG001
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"%PDF-1.4\n% stub\n")
        calls["dest"] = dest

    monkeypatch.setattr(Renderer, "render", staticmethod(_fake_render))

    res = runner.invoke(app, ["preview", spec, "--pdf"], prog_name="bits")
    assert res.exit_code == 0

    out_dir = Path(config.get("preview", "out_dir", fallback=".bitsout/preview"))
    expected_pdf = out_dir / f"{bitsfile.stem}__mass-of-the-sun__p-default.pdf"
    if not expected_pdf.exists():
        print("Preview CLI output (pdf single bit):\n", res.output)
        print("out dir:", out_dir)
        print("list out dir:", list(out_dir.glob("*")))
    assert expected_pdf.exists()
    assert calls.get("dest") == expected_pdf
