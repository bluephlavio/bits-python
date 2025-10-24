from pathlib import Path

from typer.testing import CliRunner

from bits.cli.main import app


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
    assert expected.exists()
