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

    def __init__(self, message="Error rendering template", detail=None):
        if detail:
            message = f"{message}: {detail}"
        super().__init__(message)


# Latex rendering exceptions
class LatexRenderError(BitsError):
    """Raised when a LaTeX build fails."""

    def __init__(self, message="Failed to render LaTeX", detail=None):
        if detail:
            message = f"{message}: {detail}"
        super().__init__(message)
