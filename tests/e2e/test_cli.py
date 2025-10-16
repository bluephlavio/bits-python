import importlib.metadata
import subprocess


def test_cli_version():
    result = subprocess.run(["bits", "--version"], capture_output=True, check=True)
    assert result.returncode == 0
    version = importlib.metadata.version("bits")
    assert result.stdout.decode("utf-8").strip() == f"bits {version}"


def test_cli_help():
    result = subprocess.run(["bits", "--help"], capture_output=True, check=True)
    assert result.returncode == 0
    help_output = result.stdout.decode("utf-8")
    assert "Usage: bits [OPTIONS] COMMAND [ARGS]..." in help_output


def test_cli_build(bitsfiles):
    for bitsfile in bitsfiles:
        result = subprocess.run(
            ["bits", "build", str(bitsfile)], capture_output=True, check=True
        )
        assert result.returncode == 0
