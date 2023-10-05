from __future__ import annotations

import re
from itertools import chain
from pathlib import Path
from typing import List

import frontmatter
import yaml
from jinja2 import Template

from ..bit import Bit
from ..block import Block
from ..collections import Collection
from ..config import config
from ..env import env
from ..helpers import normalize_path
from ..models import BlocksModel, TargetModel
from ..target import Target
from .registry import Registry
from .registry_factory import RegistryFactory


class RegistryFile(Registry):
    def __init__(self, path: Path, as_dep: bool = False):
        super().__init__(path)

        if not self._path.is_file():
            raise IsADirectoryError

        if not self._path.suffix == ".md":
            raise ValueError

        self.load(as_dep=as_dep)

    def load(self, as_dep: bool = False) -> None:
        post: frontmatter.Post = frontmatter.load(self._path)

        self._bits.clear()

        bits_src: List[str] = post.content.split("---")

        for bit_src in bits_src:
            try:
                bit: Bit = self._parse_bit(bit_src)
                self._bits.append(bit)
            except AttributeError:
                continue

        if not as_dep:
            self._targets.clear()

            targets_data: List[TargetModel] = map(
                lambda data: TargetModel(**data), post.metadata["targets"]
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
        with template_path.open("r", encoding="utf-8") as template_file:
            src: str = template_file.read()
            template: Template = env.from_string(src)
            return template

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

        context: dict = {k: v for k, v in data.context.items() if k not in ["blocks"]}

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
            pass

        dest: Path = self._resolve_path(data.dest or ".")
        dest = dest / f"{self._path.stem}-{name}.pdf" if dest.suffix == "" else dest

        target: Target = Target(template, context, dest, name=name, tags=tags)
        return target
