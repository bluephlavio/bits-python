from __future__ import annotations

import re
from itertools import chain
from pathlib import Path
from typing import List

import yaml
from jinja2 import Template

from ..bit import Bit
from ..block import Block
from ..collections import Collection
from ..config import config
from ..env import EnvironmentFactory
from ..helpers import normalize_path
from ..models import BlocksModel, TargetModel
from ..target import Target
from .registry import Registry
from .registry_factory import RegistryFactory

var_pattern = re.compile(r"\$\{([^}]+)\}")

yaml.add_implicit_resolver("!var", var_pattern)


def interpolated_var_constructor(loader, node):
    value = loader.construct_scalar(node)

    def replace_var(match):
        variable_name = match.group(1)
        if config.has_option("variables", variable_name):
            return config.get("variables", variable_name)
        return match.group(0)

    return var_pattern.sub(replace_var, value)


yaml.add_constructor("!var", interpolated_var_constructor)


class RegistryFile(Registry):
    def __init__(self, path: Path, as_dep: bool = False):
        super().__init__(path)

        if not self._path.is_file():
            raise IsADirectoryError

        if not self._path.suffix == ".md":
            raise ValueError

        self.load(as_dep=as_dep)

    def load(self, as_dep: bool = False) -> None:
        with open(self._path, "r", encoding="utf-8") as file:
            content = file.read()

        delimiter = "---"
        parts = content.split(delimiter)
        if len(parts) < 3:
            raise ValueError("Invalid frontmatter format")

        frontmatter_content = parts[1]
        post_content = delimiter.join(parts[2:])

        post_metadata = yaml.load(frontmatter_content, Loader=yaml.FullLoader)

        self._bits.clear()

        bits_src: List[str] = post_content.split("---")

        for bit_src in bits_src:
            try:
                bit: Bit = self._parse_bit(bit_src)
                self._bits.append(bit)
            except AttributeError:
                continue

        for bit in self._bits:
            bit.defaults = self._parse_context(bit.defaults)

        if not as_dep:
            self._targets.clear()

            targets_data: List[TargetModel] = map(
                lambda data: TargetModel(**data), post_metadata["targets"]
            )

            for target_data in targets_data:
                target: Target = self._parse_target(target_data)
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

    def _parse_bit(self, src: str) -> Bit:
        src_match: re.Match = re.match(
            r"^\s*(?P<header>[\S\s]*)\s*```latex\s*(?P<content>[\S\s]*)\s*```\s*$",
            src,
        )

        header: str = src_match.group("header").strip().replace("::", ":")
        content: str = src_match.group("content").strip()

        meta: dict = yaml.load(header, Loader=yaml.Loader)

        bit: Bit = Bit(content, **meta)
        return bit

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
