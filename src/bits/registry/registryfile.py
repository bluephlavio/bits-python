from __future__ import annotations
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List
from itertools import chain

from jinja2 import Template

from .registry import Registry
from .registry_factory import RegistryFactory
from ..block import Block
from ..collections import Collection
from ..config import config
from ..env import EnvironmentFactory
from ..helpers import normalize_path
from ..models import BlocksModel, TargetModel
from ..target import Target
from ..bit import Bit


class RegistryFile(Registry, ABC):
    # pylint: disable=unused-argument
    def __init__(self, path: Path, as_dep: bool = False):
        super().__init__(path)
        if not self._path.is_file():
            raise IsADirectoryError
        self._check_file_type()
        self.load(as_dep=as_dep)

    @abstractmethod
    def _check_file_type(self):
        pass

    @abstractmethod
    def load(self, as_dep: bool = False):
        pass

    def _resolve_path(self, path: str) -> Path:
        return normalize_path(path, relative_to=self._path)

    def _resolve_registry(self, path: str) -> Registry:
        registry_path: Path = self._resolve_path(path)
        registry: Registry = RegistryFactory.get(registry_path, as_dep=True)
        return registry

    def _resolve_template(self, path: str) -> Template:
        template_path: Path = self._resolve_path(path)
        env = EnvironmentFactory.get(templates_folder=template_path.parent)
        template: Template = env.get_template(template_path.name)
        return template

    def _parse_context(self, data: dict) -> dict:
        context: dict = {
            k: v for k, v in data.items() if k not in ["blocks", "constants"]
        }

        if "blocks" in data:
            blocks: List[Block] = list(
                chain(
                    *map(
                        self._parse_blocks,
                        map(
                            lambda blocks: BlocksModel(**blocks),
                            data["blocks"],
                        ),
                    )
                ),
            )
            context["blocks"] = blocks

        if "constants" in data:
            context["constants"] = data["constants"]

        return context

    def _parse_blocks(self, data: BlocksModel) -> List[Block]:
        registry: Registry = (
            self._resolve_registry(data.registry) if data.registry else self
        )

        bits: Collection[Bit] = registry.bits.query(**data.query.dict())

        context: dict = self._parse_context(data.context)

        metadata: dict = data.metadata

        blocks: List[Block] = [
            Block(bit, context=context, metadata=metadata) for bit in bits
        ]
        return blocks

    def _parse_target(self, data: TargetModel) -> Target:
        name: str | None = data.name
        tags: List[str] = data.tags or []

        template: Template = self._resolve_template(
            data.template or config.get("DEFAULT", "template")
        )

        context: dict = {
            k: v for k, v in data.context.items() if k not in ["blocks", "constants"]
        }

        if "blocks" in data.context:
            blocks: List[Block] = list(
                chain(
                    *map(
                        self._parse_blocks,
                        map(
                            lambda blocks: BlocksModel(**blocks),
                            data.context["blocks"],
                        ),
                    )
                ),
            )
            context["blocks"] = blocks

        if "constants" in data.context:
            context["constants"] = data.context["constants"]

        dest: Path = self._resolve_path(data.dest or ".")
        dest = dest / f"{self._path.stem}-{name}.pdf" if dest.suffix == "" else dest

        target: Target = Target(template, context, dest, name=name, tags=tags)
        return target
