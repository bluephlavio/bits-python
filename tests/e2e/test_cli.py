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
    assert result.stdout.decode("utf-8").startswith(
        "Usage: bits [OPTIONS] COMMAND [ARGS]..."
    )


def test_cli_build(bitsfiles):
    for bitsfile in bitsfiles:
        result = subprocess.run(
            ["bits", "build", str(bitsfile)], capture_output=True, check=True
        )
        assert result.returncode == 0
