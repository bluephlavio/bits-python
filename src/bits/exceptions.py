class BitsError(Exception):
    """Base class for all exceptions in the Bits package."""

    def __init__(self, message="An error occurred in the Bits package"):
        super().__init__(message)


# Registry-related exceptions
class RegistryError(BitsError):
    """Base class for registry-related errors."""

    def __init__(self, message="Registry error", path=None):
        if path:
            message = f"{message}: {path}"
        super().__init__(message)


class RegistryLoadError(RegistryError):
    """Raised when a registry cannot be loaded."""

    def __init__(self, message="Failed to load registry", path=None):
        if path:
            message = f"{message}: {path}"
        super().__init__(message)


class RegistryNotFoundError(RegistryError):
    """Raised when a registry cannot be found."""

    def __init__(self, message="Registry not found", path=None):
        if path:
            message = f"{message}: {path}"
        super().__init__(message)


class RegistryParseError(RegistryError):
    """Raised when there is an error parsing a registry file."""

    def __init__(self, message="Error parsing registry", path=None, line_number=None):
        if path and line_number:
            message = f"{message}: {path}:{line_number}"
        elif path:
            message = f"{message}: {path}"
        super().__init__(message)


class RegistryReferenceError(RegistryError):
    """Raised when a reference in a registry cannot be resolved."""

    def __init__(
        self, message="Unresolved registry reference", reference=None, path=None
    ):
        if reference and path:
            message = f"{message}: '{reference}' in {path}"
        elif reference:
            message = f"{message}: '{reference}'"
        super().__init__(message, path)


# Configuration-related exceptions
class ConfigError(BitsError):
    """Base class for configuration-related errors."""

    def __init__(self, message="Configuration error", config_item=None):
        if config_item:
            message = f"{message}: {config_item}"
        super().__init__(message)


class ConfigFileError(ConfigError):
    """Raised when a configuration file cannot be read or parsed."""

    def __init__(
        self, message="Error in configuration file", path=None, line_number=None
    ):
        if path and line_number:
            message = f"{message}: {path}:{line_number}"
        elif path:
            message = f"{message}: {path}"
        super().__init__(message)


class ConfigValueError(ConfigError):
    """Raised when a configuration value is invalid."""

    def __init__(self, message="Invalid configuration value", key=None, value=None):
        if key and value:
            message = f"{message}: {key}={value}"
        elif key:
            message = f"{message}: {key}"
        super().__init__(message)


# Template-related exceptions
class TemplateError(BitsError):
    """Base class for template-related errors."""

    def __init__(self, message="Template error"):
        super().__init__(message)


class TemplateLoadError(TemplateError):
    """Raised when a template cannot be loaded."""

    def __init__(self, message="Failed to load template", template_name=None):
        if template_name:
            message = f"{message}: {template_name}"
        super().__init__(message)


class TemplateContextError(TemplateError):
    """Raised when a template context cannot be resolved."""

    def __init__(
        self, message="Could not resolve template context", context_detail=None
    ):
        if context_detail:
            message = f"{message}: {context_detail}"
        super().__init__(message)


class TemplateRenderError(TemplateError):
    """Raised when a template cannot be rendered."""

    def __init__(
        self, message="Error rendering template", detail=None, line_number=None
    ):
        if detail and line_number:
            message = f"{message}: {detail} at line {line_number}"
        elif detail:
            message = f"{message}: {detail}"
        super().__init__(message)


# Latex rendering exceptions
class LatexRenderError(BitsError):
    """Raised when a LaTeX build fails."""

    def __init__(self, message="Failed to render LaTeX", detail=None, log_file=None):
        if detail and log_file:
            message = f"{message}: {detail} (see {log_file} for details)"
        elif detail:
            message = f"{message}: {detail}"
        super().__init__(message)


# File system related exceptions
class FileSystemError(BitsError):
    """Base class for file system related errors."""

    def __init__(self, message="File system error", path=None):
        if path:
            message = f"{message}: {path}"
        super().__init__(message)


class FileReadError(FileSystemError):
    """Raised when a file cannot be read."""

    def __init__(self, message="Failed to read file", path=None):
        super().__init__(message, path)


class FileWriteError(FileSystemError):
    """Raised when a file cannot be written."""

    def __init__(self, message="Failed to write file", path=None):
        super().__init__(message, path)


class FileWatchError(FileSystemError):
    """Raised when there is an error watching a file for changes."""

    def __init__(self, message="Error watching file", path=None):
        super().__init__(message, path)


# Build process related exceptions
class BuildError(BitsError):
    """Base class for build process related errors."""

    def __init__(self, message="Build process error", target=None):
        if target:
            message = f"{message}: {target}"
        super().__init__(message)


class BuildDependencyError(BuildError):
    """Raised when a build dependency cannot be satisfied."""

    def __init__(self, message="Missing build dependency", dependency=None):
        if dependency:
            message = f"{message}: {dependency}"
        super().__init__(message)
