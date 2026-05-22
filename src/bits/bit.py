from typing import Dict, List, Union

from jinja2 import Template

from .collections import Element
from .dialects import DialectRegistry
from .env import EnvironmentFactory
from .exceptions import DialectError, TemplateLoadError, TemplateRenderError
from .models import BitModel


class Bit(Element):
    def __init__(  # pylint: disable=too-many-arguments
        self,
        src: Union[str, Dict[str, str]],
        name: str | None = None,
        tags: List[str] | None = None,
        author: str | None = None,
        kind: str | None = None,
        level: int | None = None,
        dialect: str | None = None,
        source_path: str | None = None,
        defaults: dict | None = None,
        presets: list | None = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            tags=tags,
            author=author,
            kind=kind,
            level=level,
            dialect=dialect,
            **kwargs,
        )
        # Raw src: either a single template string or a mapping of fragments
        self.src: Union[str, Dict[str, str]] = src
        self._source_path = source_path

        self.defaults: dict = defaults or {}
        self.presets: list = presets or []

        # Pre-compile template(s)
        try:
            if self.dialect:
                self._template = None  # type: ignore[assignment]
                self._templates = {}
            elif isinstance(self.src, str):
                self._template: Template = EnvironmentFactory.get().from_string(
                    self.src
                )
                self._templates: Dict[str, Template] = {}
            else:
                self._template = None  # type: ignore[assignment]
                self._templates = {
                    key: EnvironmentFactory.get().from_string(val)
                    for key, val in self.src.items()
                }
        except Exception as err:
            raise TemplateLoadError(f"Unable to load bit source: \n\n{self}\n") from err

    def __repr__(self) -> str:
        return f"Bit(src={self.src})"

    def __str__(self) -> str:
        return self.src

    @property
    def author(self) -> str | None:
        return self._metadata["author"] if "author" in self._metadata else None

    @property
    def kind(self) -> str | None:
        return self._metadata["kind"] if "kind" in self._metadata else None

    @property
    def level(self) -> int | None:
        return self._metadata["level"] if "level" in self._metadata else None

    @property
    def dialect(self) -> str | None:
        return self._metadata["dialect"] if "dialect" in self._metadata else None

    @property
    def is_multi_fragment(self) -> bool:
        return isinstance(self.src, dict)

    @property
    def fragment_names(self) -> List[str]:
        if isinstance(self.src, dict):
            return list(self.src.keys())
        return []

    def has_fragment(self, name: str) -> bool:
        if isinstance(self.src, dict):
            return name in self.src
        return name in self._templates

    def render(self, part: str | None = None, **kwargs) -> str:
        context: dict = {**self.defaults}
        context.update(**kwargs)
        try:
            if isinstance(self.src, str):
                if self.dialect:
                    source = self._apply_dialect(self.src, context)
                    return EnvironmentFactory.get().from_string(source).render(context)
                return self._template.render(context)

            if not part:
                if self.has_fragment("default"):
                    part = "default"
                else:
                    raise TemplateRenderError(
                        "Bit has multiple fragments; specify 'part' to render one. "
                        f"Available: {', '.join(self.fragment_names)}"
                    )
            if part not in self._templates:
                if self.dialect and self.has_fragment(part):
                    source = self._apply_dialect(self.src[part], context)
                    return EnvironmentFactory.get().from_string(source).render(context)
                raise TemplateRenderError(
                    f"Unknown fragment '{part}'. Available: {', '.join(self.fragment_names)}"
                )
            return self._templates[part].render(context)
        except DialectError:
            raise
        except TemplateRenderError:
            raise
        except Exception as err:
            raise TemplateRenderError(f"Error rendering bit {self.id}") from err

    def _apply_dialect(self, source: str, context: dict) -> str:
        return DialectRegistry.transform(
            self.dialect or "",
            source,
            context=context,
            path=self._source_path,
            metadata=self._dialect_metadata(),
        )

    def _dialect_metadata(self) -> dict:
        metadata = {key: value for key, value in self._metadata.items() if key != "id_"}
        metadata["id"] = str(self.id)
        return metadata

    def to_model(self) -> BitModel:
        return BitModel(
            name=self.name,
            tags=self.tags,
            author=self.author,
            kind=self.kind,
            level=self.level,
            dialect=self.dialect,
            defaults=self.defaults,
            presets=self.presets,
            src=self.src,
        )
