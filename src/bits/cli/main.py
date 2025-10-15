import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.traceback import install

from .. import __version__
from ..registry import RegistryFactory, RegistryFile
from .helpers import initialize_registry, watch_for_changes


def _supports_unicode_output(stream) -> bool:
    """Return True if the stream can safely render unicode box characters."""
    encoding = getattr(stream, "encoding", None) or "utf-8"
    try:
        "\u2500".encode(encoding)
    except Exception:  # pragma: no cover - conservative fallback
        return False
    return True


_USE_RICH_STYLING = _supports_unicode_output(sys.stdout)

app = typer.Typer(
    rich_markup_mode="rich" if _USE_RICH_STYLING else None,
    pretty_exceptions_enable=_USE_RICH_STYLING,
    pretty_exceptions_show_locals=False,
)
console = Console(legacy_windows=not _USE_RICH_STYLING)
install(
    suppress=[SystemExit, KeyboardInterrupt],
    show_locals=_USE_RICH_STYLING,
)


def version_callback(ctx: typer.Context, param, value: bool):
    if value:
        typer.echo(f"bits {__version__}")
        ctx.exit()


@app.callback()
def common(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show the version and exit",
    ),
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
