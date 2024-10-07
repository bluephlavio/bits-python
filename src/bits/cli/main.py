import time
from pathlib import Path
from typing import Optional

import typer

from .. import __version__
from ..registry import Registry, RegistryFactory, RegistryFile

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

        def reload_and_rerender(event):  # pylint: disable=unused-argument
            if not (
                event.src_path.endswith(".yml")
                or event.src_path.endswith(".yaml")
                or event.src_path.endswith(".md")
            ):
                return
            registry.load(as_dep=False)
            registry.render()

        registry.add_listener(reload_and_rerender, recursive=True)
        registry.watch()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            registry.stop()


@app.command(name="convert")
def convert(
    src: Path,
    out: Optional[Path] = typer.Option(None),
    fmt: Optional[str] = typer.Option(None),
):
    if out is None:
        if fmt is None:
            raise typer.BadParameter("Either --out or --fmt must be provided")
        out = src.with_suffix(f".{fmt}")

    registryfile: RegistryFile = RegistryFactory.get(src)
    registryfile.dump(out)
