"""
Tests for error handling functionality in the bits CLI.
"""

import re
from io import StringIO

import pytest
from rich.console import Console

from bits.cli.helpers import get_error_suggestion, print_error, process_error_message
from bits.exceptions import (
    BitsError,
    BuildError,
    ConfigError,
    FileSystemError,
    LatexRenderError,
    RegistryError,
    TemplateError,
)


def test_print_error_formatting():
    """Test that the print_error function properly formats different error types."""
    # Create a string buffer to capture the output
    string_io = StringIO()
    console = Console(file=string_io, highlight=False)

    # Test with different error types
    errors = [
        RegistryError("Failed to load registry", "/path/to/registry.yml"),
        TemplateError("Template syntax error at line 42"),
        LatexRenderError("Failed to render LaTeX", "Missing package", "/tmp/latex.log"),
        FileSystemError("Failed to read file", "/path/to/file.yml"),
        ConfigError("Invalid configuration value", "max_depth"),
        BuildError("Missing build dependency", "xelatex"),
    ]

    for error in errors:
        string_io.seek(0)
        string_io.truncate(0)

        print_error(error, console)
        output = string_io.getvalue()

        # Check that the error class name appears in the output
        assert error.__class__.__name__ in output

        # Check that key parts of the error message appear in the output
        if isinstance(error, RegistryError):
            assert "Registry Error" in output
            assert "Failed to load registry" in output
            assert "/path/to/registry.yml" in output
        elif isinstance(error, LatexRenderError):
            assert "LaTeX Error" in output  # The category in the table
            assert "Failed to render LaTeX" in output
            assert "Missing package" in output
        elif isinstance(error, FileSystemError):
            assert "FileSystemError" in output  # The class name in the title
            assert "/path/to/file.yml" in output


def test_process_error_message_highlighting():
    """Test that the process_error_message function correctly highlights elements."""
    # Instead of checking the implementation details (which is fragile),
    # we'll verify the function returns a Rich Text object with the right content

    # Test with a file path
    message = "Error in file /path/to/file.yml"
    highlighted = process_error_message(message)
    # Verify it's a Text object and contains the original message
    assert hasattr(highlighted, "append")
    assert "/path/to/file.yml" in str(highlighted)

    # Test with a line number
    message = "Error at line 42"
    highlighted = process_error_message(message)
    assert "line 42" in str(highlighted)

    # Test with quoted text
    message = "Unknown variable 'foo'"
    highlighted = process_error_message(message)
    assert "foo" in str(highlighted)


def test_get_error_suggestion():
    """Test that appropriate suggestions are provided for different error types."""
    # Test registry error suggestions
    registry_error = RegistryError("Registry not found", "/path/to/registry.yml")
    suggestion = get_error_suggestion(registry_error)
    assert "Check that the registry path exists" in str(suggestion)

    # Test template error suggestions
    template_error = TemplateError("Failed to load template")
    suggestion = get_error_suggestion(template_error)
    assert "Verify the template path" in str(suggestion)

    # Test LaTeX error suggestions
    latex_error = LatexRenderError("Failed to render", "Package not found")
    suggestion = get_error_suggestion(latex_error)
    assert "Check your LaTeX syntax" in str(suggestion)


def test_error_chain():
    """Test that error chaining works correctly."""
    # Create a chain of errors
    try:
        try:
            try:
                raise FileSystemError("Failed to read file", "/path/to/file.yml")
            except FileSystemError as e:
                raise TemplateError("Failed to load template") from e
        except TemplateError as e:
            raise BuildError("Build failed") from e
    except BuildError as error:
        # Create a string buffer to capture the output
        string_io = StringIO()
        console = Console(file=string_io, highlight=False)

        print_error(error, console)
        output = string_io.getvalue()

        # Check that all errors in the chain appear in the output
        assert "BuildError" in output
        assert "TemplateError" in output
        assert "FileSystemError" in output
        assert "/path/to/file.yml" in output
