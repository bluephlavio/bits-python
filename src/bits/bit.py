from typing import List

from jinja2 import Template

from .collections import Element
from .env import EnvironmentFactory
from .exceptions import TemplateLoadError, TemplateRenderError
from .models import BitModel


class Bit(Element):
    def __init__(  # pylint: disable=too-many-arguments
        self,
        src: str,
        name: str | None = None,
        tags: List[str] | None = None,
        author: str | None = None,
        kind: str | None = None,
        level: int | None = None,
        defaults: dict | None = None,
        **kwargs,
    ):
        super().__init__(
            name=name, tags=tags, author=author, kind=kind, level=level, **kwargs
        )

        self.src: str = src

        self.defaults: dict = defaults or {}

        try:
            self.template: Template = EnvironmentFactory.get().from_string(self.src)
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

    def render(self, **kwargs) -> str:
        context: dict = {**self.defaults}
        context.update(**kwargs)
        try:
            return self.template.render(context)
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
            src=self.src,
        )
