import time
from pathlib import Path

import typer

from .. import __version__
from ..registry import Registry, RegistryFactory

app = typer.Typer()


def version_callback(value: bool):
    if value:
        typer.echo(f"bits {__version__}")
        raise typer.Exit()


@app.callback()
def common(
    version: bool = typer.Option(None, "--version", callback=version_callback)
):  # pylint: disable=unused-argument
    pass


@app.command(name="build")
def render(path: Path, watch: bool = typer.Option(False)):
    registry: Registry = RegistryFactory.get(path)
    registry.render()

    if watch:
        registry.watch()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            registry.stop()
