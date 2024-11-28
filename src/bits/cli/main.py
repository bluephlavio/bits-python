from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.traceback import install

from .. import __version__
from ..registry import RegistryFactory, RegistryFile
from .helpers import initialize_registry, watch_for_changes

app = typer.Typer()
console = Console()
install()


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
def render(
    path: Path,
    watch: bool = typer.Option(False),
    output_tex: bool = typer.Option(False),
):
    console.print("[bold green]Starting build process...[/bold green]")

    registry = initialize_registry(path, console, watch, output_tex)

    if watch:
        console.print("[bold yellow]Watching for file changes...[/bold yellow]")
        watch_for_changes(registry, console, output_tex)


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
