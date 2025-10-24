import importlib.metadata
from typer.testing import CliRunner

from bits.cli.main import app


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
        result = runner.invoke(app, ["build", str(bitsfile)], prog_name="bits")
        assert result.exit_code == 0


def test_cli_build_single_target(bitsfiles):
    # Pick a known file with target 't1'
    runner = CliRunner()
    for bitsfile in bitsfiles:
        if bitsfile.name == "bits-presets.yaml":
            target_spec = f"{bitsfile}::t1"
            result = runner.invoke(app, ["build", target_spec, "--tex"], prog_name="bits")
            assert result.exit_code == 0
            break
