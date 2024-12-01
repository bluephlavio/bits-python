import re
import time
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ..exceptions import BitsError
from ..registry import Registry, RegistryFactory


def print_error(err: BitsError, console: Console):
    error_messages = []
    current = err
    path_pattern = re.compile(r"(/[^ ]*)")

    while current:
        message = str(current)
        highlighted_message = Text()
        last_end = 0

        for match in path_pattern.finditer(message):
            start, end = match.span()
            highlighted_message.append(message[start:end], "bold blue underline")
            last_end = end

        highlighted_message.append(message[last_end:])
        error_messages.append(
            Text.assemble(
                (f"{current.__class__.__name__}: ", "bold red"), highlighted_message
            )
        )
        current = current.__cause__ or current.__context__

    error_message = Text("\n").join(error_messages)
    panel = Panel(error_message, title="Error", expand=False, border_style="red")
    console.print(panel)


def print_render_summary(registry: Registry, console: Console):
    summary_lines = []
    for target in registry.targets:
        line = Text.assemble(
            (f"{target.name} (RENDERED): ", "bold green"),
            (str(target.dest), "bold blue underline"),
        )
        summary_lines.append(line)

    summary_message = Text("\n").join(summary_lines)
    panel = Panel(
        summary_message, title="Render Summary", expand=False, border_style="green"
    )
    console.print(panel)


def initialize_registry(path: Path, console: Console, watch: bool, output_tex: bool):
    registry = None
    last_error = None
    waiting_message_printed = False

    while registry is None:
        try:
            registry = RegistryFactory.get(path)
            console.print("[bold green]Rendering...[/bold green]")
            registry.render(output_tex=output_tex)
            console.print("[bold green]Render complete.[/bold green]")
            last_error = None
            print_render_summary(registry, console)
        except Exception as err:  # pylint: disable=broad-except
            if str(err) != last_error:
                print_error(err, console)
                last_error = str(err)
            if not watch:
                raise typer.Exit(code=1)
            if not waiting_message_printed:
                console.print("[bold yellow]Waiting for file changes...[/bold yellow]")
                waiting_message_printed = True
            time.sleep(1)

    return registry


def watch_for_changes(registry: Registry, console: Console, output_tex: bool):
    def reload_and_rerender(event):  # pylint: disable=unused-argument
        if not (
            event.src_path.endswith(".yml")
            or event.src_path.endswith(".yaml")
            or event.src_path.endswith(".md")
        ):
            return
        console.print(
            f"[bold green]File change detected: {event.src_path}[/bold green]"
        )
        try:
            console.print("[bold green]Re-rendering...[/bold green]")
            registry.load(as_dep=False)
            registry.render(output_tex=output_tex)
            console.print("[bold green]Re-render complete.[/bold green]")
            print_render_summary(registry, console)
        except Exception as err:  # pylint: disable=broad-except
            print_error(err, console)

    registry.add_listener(reload_and_rerender, recursive=True)
    registry.watch()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("[bold red]Process stopped by user.[/bold red]")
        registry.stop()
    except Exception as err:  # pylint: disable=broad-except
        print_error(err, console)
