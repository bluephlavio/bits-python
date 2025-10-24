import re
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from ..exceptions import (
    BitsError,
    BuildError,
    ConfigError,
    FileSystemError,
    LatexRenderError,
    RegistryError,
    TemplateError,
)
from ..registry import Registry, RegistryFactory


def print_error(err: Exception, console: Console):
    """
    Print a detailed error message with formatting.

    Args:
        err: The exception that was caught
        console: Rich console instance for formatted output
    """
    if not isinstance(err, BitsError):
        # For non-BitsError exceptions, wrap them in a panel with traceback
        error_panel = Panel(
            Text.from_markup(
                f"[bold red]{err.__class__.__name__}:[/bold red] {str(err)}\n\n"
            )
            + Text(traceback.format_exc()),
            title="Unexpected Error",
            border_style="red",
            expand=False,
        )
        console.print(error_panel)
        return

    # Create the main error table
    error_table = Table(
        box=box.ROUNDED, show_header=False, expand=True, border_style="red"
    )
    error_table.add_column("Category", style="bold red", width=15)
    error_table.add_column("Details", style="white")

    # Get the error category based on the exception type
    error_category = "Error"
    if isinstance(err, RegistryError):
        error_category = "Registry Error"
    elif isinstance(err, TemplateError):
        error_category = "Template Error"
    elif isinstance(err, LatexRenderError):
        error_category = "LaTeX Error"
    elif isinstance(err, FileSystemError):
        error_category = "File System Error"
    elif isinstance(err, ConfigError):
        error_category = "Config Error"
    elif isinstance(err, BuildError):
        error_category = "Build Error"

    # Add the error details
    message = str(err)

    # Process the message to highlight paths, line numbers, etc.
    highlighted_message = process_error_message(message)

    error_table.add_row(error_category, highlighted_message)

    # Add suggestions for fixing the error based on its type
    suggestion = get_error_suggestion(err)
    if suggestion:
        error_table.add_row("Suggestion", suggestion)

    # Get the error cause chain
    causes = get_error_causes(err)
    if causes:
        error_table.add_row("Caused By", Text("\n").join(causes))

    # Create the final panel with the error table
    error_panel = Panel(
        error_table, title=f"{err.__class__.__name__}", border_style="red", expand=False
    )

    console.print(error_panel)


def process_error_message(message: str) -> Text:
    """
    Process an error message to highlight paths, line numbers, etc.

    Args:
        message: The error message to process

    Returns:
        A Rich Text object with highlighted components
    """
    highlighted_message = Text()

    # Pattern for file paths
    path_pattern = re.compile(r"(/[^ :,]*)")

    # Pattern for line numbers (e.g., "line 42" or "line 42:")
    line_pattern = re.compile(r"(line \d+)")

    # Pattern for quoted text
    quote_pattern = re.compile(r"'([^']*)'")

    last_end = 0

    # Highlight file paths
    for match in path_pattern.finditer(message):
        start, end = match.span()
        highlighted_message.append(message[last_end:start])
        highlighted_message.append(message[start:end], "bold blue underline")
        last_end = end

    temp_message = str(highlighted_message) + message[last_end:]
    highlighted_message = Text()
    last_end = 0

    # Highlight line numbers
    for match in line_pattern.finditer(temp_message):
        start, end = match.span()
        highlighted_message.append(temp_message[last_end:start])
        highlighted_message.append(temp_message[start:end], "bold yellow")
        last_end = end

    temp_message = str(highlighted_message) + temp_message[last_end:]
    highlighted_message = Text()
    last_end = 0

    # Highlight quoted text
    for match in quote_pattern.finditer(temp_message):
        start, end = match.span()
        full_match = match.group(0)  # The entire match including quotes
        quoted_text = match.group(1)  # Just the text inside quotes

        highlighted_message.append(temp_message[last_end:start])
        highlighted_message.append("'", style="")
        highlighted_message.append(quoted_text, "italic cyan")
        highlighted_message.append("'", style="")
        last_end = end

    highlighted_message.append(temp_message[last_end:])

    return highlighted_message


def get_error_suggestion(err: BitsError) -> Optional[Text]:
    """
    Get a suggestion for fixing an error based on its type.

    Args:
        err: The exception that was caught

    Returns:
        A suggestion message or None if no specific suggestion is available
    """
    suggestion = Text()

    if isinstance(err, RegistryError):
        if "not found" in str(err).lower():
            suggestion.append("Check that the registry path exists and is accessible.")
        elif "parse" in str(err).lower():
            suggestion.append("Check your YAML/Markdown syntax for errors.")
        elif "reference" in str(err).lower():
            suggestion.append(
                "Ensure all referenced registries exist and are correctly specified."
            )

    elif isinstance(err, TemplateError):
        if "load" in str(err).lower():
            suggestion.append("Verify the template path and permissions.")
        elif "context" in str(err).lower():
            suggestion.append(
                "Check that all required template variables are provided."
            )
        elif "render" in str(err).lower():
            suggestion.append("Check the template syntax and variables.")

    elif isinstance(err, LatexRenderError):
        suggestion.append(
            "Check your LaTeX syntax and ensure all required packages are installed."
        )
        if "log_file" in str(err).lower():
            log_file_match = re.search(r"\(see (.*) for details\)", str(err))
            if log_file_match:
                suggestion.append("\nReview the LaTeX log file for specific errors: ")
                suggestion.append(log_file_match.group(1), "bold blue underline")

    elif isinstance(err, FileSystemError):
        if "read" in str(err).lower():
            suggestion.append("Check file permissions and that the file exists.")
        elif "write" in str(err).lower():
            suggestion.append("Check directory permissions and available disk space.")
        elif "watch" in str(err).lower():
            suggestion.append(
                "Ensure the file system supports file watching and the path is valid."
            )

    elif isinstance(err, ConfigError):
        suggestion.append(
            "Check your configuration file for syntax errors or invalid values."
        )

    elif isinstance(err, BuildError):
        if "dependency" in str(err).lower():
            suggestion.append(
                "Ensure all required dependencies are installed and properly configured."
            )
        else:
            suggestion.append("Check your build configuration and environment setup.")

    return suggestion if suggestion else None


def get_error_causes(err: Exception) -> List[Text]:
    """
    Get a list of error causes from the exception chain.

    Args:
        err: The exception that was caught

    Returns:
        A list of formatted error cause messages
    """
    causes = []
    current = err.__cause__ or err.__context__

    while current:
        cause_message = Text.assemble(
            (f"{current.__class__.__name__}: ", "bold red"),
            process_error_message(str(current)),
        )
        causes.append(cause_message)
        current = current.__cause__ or current.__context__

    return causes


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


def initialize_registry(
    path: Path,
    console: Console,
    watch: bool,
    output_tex: bool,
    *,
    pdf: bool | None = None,
    tex: bool | None = None,
    both: bool = False,
    build_dir: Path | None = None,
    intermediates_dir: Path | None = None,
    keep_intermediates: str = "none",
    unique_strategy: str | None = None,
):
    """
    Initialize a registry from a path and render its targets.

    This function is designed to be resilient in watch mode, continuously trying
    to initialize the registry until successful or until manually interrupted.

    Args:
        path: Path to the registry file or directory
        console: Rich console instance for formatted output
        watch: Whether to continue trying if initialization fails
        output_tex: Whether to output TeX files

    Returns:
        Initialized Registry instance

    Raises:
        typer.Exit: If initialization fails and watch mode is not enabled
    """
    registry = None
    last_error = None
    waiting_message_printed = False
    max_retries = 3
    retry_count = 0

    console.print(
        f"[bold blue]Initializing registry from: [underline]{path}[/underline][/bold blue]"
    )

    while registry is None:
        try:
            # Try to create and initialize the registry
            console.print("[bold]Loading registry...[/bold]")
            registry = RegistryFactory.get(path)

            # Try to render the registry
            console.rule("[bold]Build Started")
            console.print("[bold green]Rendering...[/bold green]")
            registry.render(
                output_tex=output_tex,
                pdf=pdf,
                tex=tex,
                both=both,
                build_dir=build_dir,
                intermediates_dir=intermediates_dir,
                keep_intermediates=keep_intermediates,
                unique_strategy=unique_strategy,
            )
            console.print("[bold green]Render complete.[/bold green]")
            print_render_summary(registry, console)
            console.rule("[bold]Build Completed")

            # Reset error tracking since we succeeded
            last_error = None

        except Exception as err:  # pylint: disable=broad-except
            # Only print the error if it's different from the last one
            error_str = str(err)
            if error_str != last_error:
                print_error(err, console)
                last_error = error_str

            retry_count += 1

            # If we're not in watch mode, try a few times then exit
            if not watch:
                if retry_count < max_retries:
                    console.print(
                        f"[bold yellow]Initialization failed. Retrying ({retry_count}/{max_retries})...[/bold yellow]"
                    )
                    time.sleep(1)
                else:
                    console.print(
                        "[bold red]Failed to initialize registry after multiple attempts. Exiting.[/bold red]"
                    )
                    raise typer.Exit(code=1)
            else:
                # In watch mode, we'll keep trying indefinitely
                if not waiting_message_printed:
                    console.print(
                        "[bold yellow]Waiting for file changes...[/bold yellow]"
                    )
                    waiting_message_printed = True
                time.sleep(1)

    return registry


def watch_for_changes(registry: Registry, console: Console, output_tex: bool):
    """
    Watch for file changes and trigger re-rendering when changes are detected.

    This function is designed to be resilient to errors, always continuing to
    watch for changes even if errors occur during rendering.

    Args:
        registry: The registry to watch and re-render
        console: Rich console instance for formatted output
        output_tex: Whether to output TeX files
    """
    last_error = None  # Track the last error to avoid repeating the same error messages

    def reload_and_rerender(event):  # pylint: disable=unused-argument
        nonlocal last_error

        # Only respond to changes in relevant files
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

            # Create a divider for visual separation
            console.rule("[bold]Build Started")

            # Try to load and render the registry
            registry.load(as_dep=False)
            registry.render(
                output_tex=output_tex,
                pdf=pdf,
                tex=tex,
                both=both,
                build_dir=build_dir,
                intermediates_dir=intermediates_dir,
                keep_intermediates=keep_intermediates,
                unique_strategy=unique_strategy,
            )

            console.print("[bold green]Re-render complete.[/bold green]")
            print_render_summary(registry, console)

            # Clear the last error since we succeeded
            last_error = None

        except Exception as err:  # pylint: disable=broad-except
            # Only print detailed error if it's different from the last one
            # to avoid spamming the console with the same error
            error_str = str(err)
            if error_str != last_error:
                print_error(err, console)
                last_error = error_str

            console.print("[bold yellow]Waiting for file changes...[/bold yellow]")
        finally:
            # Create a divider to show the build process is complete
            console.rule("[bold]Build Completed")

    # Set up the file watching
    try:
        registry.add_listener(reload_and_rerender, recursive=True)
        registry.watch()
        console.print("[bold yellow]Watching for file changes...[/bold yellow]")
    except Exception as err:  # pylint: disable=broad-except
        print_error(err, console)
        console.print("[bold red]Failed to set up file watching. Exiting.[/bold red]")
        raise typer.Exit(code=1)

    # Main watch loop that should never exit unless explicitly stopped
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            console.print("[bold red]Process stopped by user.[/bold red]")
            try:
                registry.stop()
            except Exception as err:  # pylint: disable=broad-except
                print_error(err, console)
            raise typer.Exit(0)
        except Exception as err:  # pylint: disable=broad-except
            print_error(err, console)
            console.print(
                "[bold yellow]Encountered error in watch loop, continuing to watch...[/bold yellow]"
            )
            # Continue the loop even if an error occurs
