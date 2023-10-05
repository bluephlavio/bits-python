from typing import List

from jinja2 import Template

from .collections import Element
from .env import env


class Bit(Element):
    def __init__(  # pylint: disable=too-many-arguments
        self,
        src: str,
        name: str | None = None,
        tags: List[str] | None = None,
        author: str | None = None,
        kind: str | None = None,
        level: int | None = None,
        constants: List[str] | None = None,
        defaults: dict | None = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            tags=tags,
            author=author,
            kind=kind,
            level=level,
            **kwargs
        )

        self.src: str = src

        self.constants: List[str] = constants or []
        self.defaults: dict = defaults or {}

        self.template: Template = env.from_string(self.src)

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
        return self.template.render(context)
