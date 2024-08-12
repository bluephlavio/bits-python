from __future__ import annotations
from pathlib import Path
from typing import List

from jinja2 import Template

from .registry import Registry
from .registry_factory import RegistryFactory
from .registryfile_parsers import RegistryFileMdParser, RegistryFileYamlParser
from ..block import Block
from ..collections import Collection
from ..config import config
from ..env import EnvironmentFactory
from ..helpers import normalize_path
from ..models import BlocksModel, TargetModel, RegistryDataModel
from ..target import Target
from ..bit import Bit


class RegistryFile(Registry):
    # pylint: disable=unused-argument
    def __init__(self, path: Path, as_dep: bool = False):
        super().__init__(path)
        if not self._path.is_file():
            raise IsADirectoryError
        if self._path.suffix in [".yml", ".yaml"]:
            self._parser = RegistryFileYamlParser()
        elif self._path.suffix == ".md":
            self._parser = RegistryFileMdParser()
        else:
            raise ValueError(f"Unsupported file format: {self._path.suffix}")
        self.load(as_dep=as_dep)

    def load(self, as_dep: bool = False):
        registryfile_model: RegistryDataModel = self._parser.parse(self._path)

        for bit_model in registryfile_model.bits:
            src: str = bit_model.src
            meta: dict = bit_model.dict(exclude={"src"})
            bit: Bit = Bit(src, **meta)
            self._bits.append(bit)

        for bit in self._bits:
            bit.defaults = self._resolve_context(bit.defaults)

        if not as_dep:
            for target_model in registryfile_model.targets:
                target: Target = self._resolve_target(target_model)
                self._targets.append(target)

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

    def _resolve_context(self, data: dict) -> dict:
        context: dict = {
            k: v for k, v in data.items() if k not in ["blocks", "constants"]
        }

        if "blocks" in data:
            blocks: List[Block] = [
            block
            for blocks_data in data["blocks"]
            for block in self._resolve_blocks(BlocksModel(**blocks_data))
            ]
            context["blocks"] = blocks

        if "constants" in data:
            context["constants"] = data["constants"]

        return context

    def _resolve_blocks(self, data: BlocksModel) -> List[Block]:
        registry: Registry = (
            self._resolve_registry(data.registry) if data.registry else self
        )

        bits: Collection[Bit] = registry.bits.query(**data.query.dict())

        context: dict = self._resolve_context(data.context)

        metadata: dict = data.metadata

        blocks: List[Block] = [
            Block(bit, context=context, metadata=metadata) for bit in bits
        ]
        return blocks

    def _resolve_target(self, data: TargetModel) -> Target:
        name: str | None = data.name
        tags: List[str] = data.tags or []

        template: Template = self._resolve_template(
            data.template or config.get("DEFAULT", "template")
        )

        context: dict = self._resolve_context(data.context)

        dest: Path = self._resolve_path(data.dest or ".")
        dest = dest / f"{self._path.stem}-{name}.pdf" if dest.suffix == "" else dest

        target: Target = Target(template, context, dest, name=name, tags=tags)
        return target
