from __future__ import annotations

from pathlib import Path
from typing import Callable, List

import jinja2

from ..bit import Bit
from ..block import Block
from ..collections import Collection
from ..config import config
from ..constant import Constant
from ..env import EnvironmentFactory
from ..exceptions import RegistryLoadError, TemplateContextError, TemplateLoadError
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
from ..watcher import Watcher
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
        self._watcher: Watcher = Watcher(self._path)
        self._parser = RegistryFileParserFactory.get(self._path)
        self.load(as_dep=as_dep)

    def load(self, as_dep: bool = False):
        try:
            with self._load_lock:
                self.clear_registry()

                self.registryfile_model: RegistryDataModel = self._parser.parse(
                    self._path
                )

                common_tags: List[str] = self.registryfile_model.tags or []

                (
                    imported_bits,
                    imported_constants,
                    imported_targets,
                ) = self._import_registry_data(self.registryfile_model.imports)

                self._load_bits(self.registryfile_model.bits, common_tags)
                self._bits.extend(imported_bits)

                self._load_constants(self.registryfile_model.constants, common_tags)
                self._constants.extend(imported_constants)

                if not as_dep:
                    self._load_targets(self.registryfile_model.targets, common_tags)
                    self._targets.extend(imported_targets)
        except Exception as err:
            raise RegistryLoadError(path=self._path) from err

    def _load_bits(self, bit_models: List[BitModel], common_tags: List[str]):
        for bit_model in bit_models:
            src: str = bit_model.src
            meta: dict = bit_model.dict(exclude={"src"})
            bit: Bit = Bit(src, **meta)
            bit.tags.extend(common_tags)
            self._bits.append(bit)

        for bit in self._bits:
            try:
                bit.defaults = self._resolve_context(bit.defaults)
            except Exception as err:
                raise TemplateContextError(
                    f"Could not resolve bit defaults: \n\n{bit.defaults}\n"
                ) from err

    def _load_constants(
        self, constant_models: List[ConstantModel], common_tags: List[str]
    ):
        for constant_model in constant_models:
            constant: Constant = Constant.from_model(constant_model)
            constant.tags.extend(common_tags)
            self._constants.append(constant)

    def _load_targets(self, target_models: List[TargetModel], common_tags: List[str]):
        for target_model in target_models:
            target: Target = self._resolve_target(target_model)
            target.tags.extend(common_tags)
            self._targets.append(target)

    def _import_registry_data(self, imports):
        imported_bits: List[Bit] = []
        imported_constants: List[Constant] = []
        imported_targets: List[Target] = []

        for import_entry in imports:
            imported_registry = self._resolve_registry(import_entry["registry"])
            imported_bits.extend(imported_registry.bits)
            imported_constants.extend(imported_registry.constants)
            imported_targets.extend(imported_registry.targets)

        return imported_bits, imported_constants, imported_targets

    def _resolve_path(self, path: str) -> Path:
        return normalize_path(path, relative_to=self._path)

    def _resolve_registry(self, path: str) -> Registry:
        registry_path: Path = self._resolve_path(path)
        registry: Registry = RegistryFactory.get(registry_path, as_dep=True)
        self.add_dep(registry)
        return registry

    def _resolve_template(self, path: str) -> jinja2.Template:
        try:
            template_path: Path = self._resolve_path(path)
            env = EnvironmentFactory.get(templates_folder=template_path.parent)
            template: jinja2.Template = env.get_template(template_path.name)
            return template
        except Exception as err:
            raise TemplateLoadError(
                f"Error loading template at {template_path}"
            ) from err

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

        if data.query:
            bits: Collection[Bit] = registry.bits.query(**data.query.dict())
        else:
            bits: Collection[Bit] = registry.bits

        try:
            context: dict = self._resolve_context(data.context)
        except Exception as err:
            raise TemplateContextError("Could not resolve block context.") from err

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

        try:
            context: dict = self._resolve_context(data.context)
        except Exception as err:
            raise TemplateContextError("Could not resolve target context.") from err

        dest: Path = self._resolve_path(data.dest or ".")
        dest = dest / f"{self._path.stem}-{name}.pdf" if dest.suffix == "" else dest

        target: Target = Target(template, context, dest, name=name, tags=tags)
        return target

    def to_registry_data_model(self) -> RegistryDataModel:
        bits = [bit.to_bit_model() for bit in self.bits]
        constants = [constant.to_constant_model() for constant in self.constants]
        targets = [target.to_target_model() for target in self.targets]
        return RegistryDataModel(bits=bits, constants=constants, targets=targets)

    def dump(self, path: Path):
        dumper = RegistryFileDumperFactory.get(path)
        dumper.dump(self.registryfile_model, path)

    def add_listener(self, on_event: Callable, recursive=True) -> None:
        self._watcher.add_listener(on_event)
        if recursive:
            for dep in self._deps:
                dep.add_listener(on_event, recursive=True)

    def watch(self, recursive=True) -> None:
        self._watcher.start()
        if recursive:
            for dep in self._deps:
                dep.watch(recursive=recursive)

    def stop(self, recursive=True) -> None:
        self._watcher.stop()
        if recursive:
            for dep in self._deps:
                dep.stop(recursive=True)
