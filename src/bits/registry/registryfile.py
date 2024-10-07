from __future__ import annotations

from pathlib import Path
from typing import List

import jinja2

from ..bit import Bit
from ..block import Block
from ..collections import Collection
from ..config import config
from ..constant import Constant
from ..env import EnvironmentFactory
from ..helpers import normalize_path
from ..models import (
    BitModel,
    BlocksModel,
    ConstantModel,
    ConstantsModel,
    RegistryDataModel,
    TargetModel,
)
from ..target import Target
from .registry import Registry
from .registry_factory import RegistryFactory
from .registryfile_dumpers import RegistryFileDumperFactory
from .registryfile_parsers import RegistryFileParserFactory


class RegistryFile(Registry):
    # pylint: disable=unused-argument
    def __init__(self, path: Path, as_dep: bool = False):
        super().__init__(path)
        if not self._path.is_file():
            raise IsADirectoryError
        self._parser = RegistryFileParserFactory.get(self._path)
        self.load(as_dep=as_dep)

    def load(self, as_dep: bool = False):
        with self._load_lock:
            registryfile_model: RegistryDataModel = self._parser.parse(self._path)

            self._bits.clear()
            self._constants.clear()
            self._targets.clear()

            for bit_model in registryfile_model.bits:
                src: str = bit_model.src
                meta: dict = bit_model.dict(exclude={"src"})
                bit: Bit = Bit(src, **meta)
                self._bits.append(bit)

            for bit in self._bits:
                bit.defaults = self._resolve_context(bit.defaults)

            for constant_model in registryfile_model.constants:
                constant: Constant = Constant.from_model(constant_model)
                self._constants.append(constant)

            if not as_dep:
                for target_model in registryfile_model.targets:
                    target: Target = self._resolve_target(target_model)
                    self._targets.append(target)

    def _resolve_path(self, path: str) -> Path:
        return normalize_path(path, relative_to=self._path)

    def _resolve_registry(self, path: str) -> Registry:
        registry_path: Path = self._resolve_path(path)
        registry: Registry = RegistryFactory.get(registry_path, as_dep=True)
        self.add_dep(registry)
        return registry

    def _resolve_template(self, path: str) -> jinja2.Template:
        template_path: Path = self._resolve_path(path)
        env = EnvironmentFactory.get(templates_folder=template_path.parent)
        template: jinja2.Template = env.get_template(template_path.name)
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
            constants: List[Constant] = [
                constant
                for constants_data in data["constants"]
                for constant in self._resolve_constants(
                    ConstantsModel(**constants_data)
                )
            ]
            context["constants"] = constants

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

    def _resolve_constants(self, data: ConstantsModel) -> List[Constant]:
        registry: Registry = (
            self._resolve_registry(data.registry) if data.registry else self
        )

        constants: List[Constant] = registry.constants.query(**data.query.dict())

        return constants

    def _resolve_target(self, data: TargetModel) -> Target:
        name: str | None = data.name
        tags: List[str] = data.tags or []

        template: jinja2.Template = self._resolve_template(
            data.template or config.get("DEFAULT", "template")
        )

        context: dict = self._resolve_context(data.context)

        dest: Path = self._resolve_path(data.dest or ".")
        dest = dest / f"{self._path.stem}-{name}.pdf" if dest.suffix == "" else dest

        target: Target = Target(template, context, dest, name=name, tags=tags)
        return target

    def to_registry_data_model(self) -> RegistryDataModel:
        bits = [bit.to_bit_model() for bit in self.bits]
        targets = [target.to_target_model() for target in self.targets]
        return RegistryDataModel(bits=bits, targets=targets)

    def dump(self, path: Path):
        dumper = RegistryFileDumperFactory.get(path)
        bits: List[BitModel] = [bit.to_model() for bit in self.bits]
        constants: List[ConstantModel] = [
            constant.to_model() for constant in self.constants
        ]
        targets: List[TargetModel] = [target.to_model() for target in self.targets]
        registry_data_model: RegistryDataModel = RegistryDataModel(
            bits=bits, constants=constants, targets=targets
        )
        dumper.dump(registry_data_model, path)
