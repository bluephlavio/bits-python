from typing import Dict, List, Union

from jinja2 import Template

from .collections import Element
from .env import EnvironmentFactory
from .exceptions import TemplateLoadError, TemplateRenderError
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
        defaults: dict | None = None,
        presets: list | None = None,
        **kwargs,
    ):
        super().__init__(
            name=name, tags=tags, author=author, kind=kind, level=level, **kwargs
        )
        # Raw src: either a single template string or a mapping of fragments
        self.src: Union[str, Dict[str, str]] = src

        self.defaults: dict = defaults or {}
        self.presets: list = presets or []

        # Pre-compile template(s)
        try:
            if isinstance(self.src, str):
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
            raise TemplateLoadError(
                f"Unable to load bit source: \n\n{self}\n"
            ) from err

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
    def is_multi_fragment(self) -> bool:
        return isinstance(self.src, dict)

    @property
    def fragment_names(self) -> List[str]:
        if isinstance(self.src, dict):
            return list(self.src.keys())
        return []

    def render(self, part: str | None = None, **kwargs) -> str:
        context: dict = {**self.defaults}
        context.update(**kwargs)
        try:
            if isinstance(self.src, str):
                return self._template.render(context)
            # Multi-fragment: require explicit part
            if not part:
                raise TemplateRenderError(
                    "Bit has multiple fragments; specify 'part' to render one. "
                    f"Available: {', '.join(self.fragment_names)}"
                )
            if part not in self._templates:
                raise TemplateRenderError(
                    f"Unknown fragment '{part}'. Available: {', '.join(self.fragment_names)}"
                )
            return self._templates[part].render(context)
        except TemplateRenderError:
            raise
        except Exception as err:
            raise TemplateRenderError(f"Error rendering bit {self.id}") from err

    def to_model(self) -> BitModel:
        return BitModel(
            name=self.name,
            tags=self.tags,
            author=self.author,
            kind=self.kind,
            level=self.level,
            defaults=self.defaults,
            presets=self.presets,
            src=self.src,
        )
