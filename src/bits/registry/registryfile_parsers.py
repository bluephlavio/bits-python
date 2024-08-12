from abc import ABC, abstractmethod
import re
from typing import List
from pathlib import Path

from ..models import RegistryDataModel, BitModel, TargetModel
from ..yaml_loader import load_yaml


class RegistryFileParser(ABC):
    @abstractmethod
    def parse(self, path: Path) -> RegistryDataModel:
        pass


class RegistryFileMdParser(RegistryFileParser):
    def _parse_bit(self, src: str) -> BitModel:
        src_match: re.Match = re.match(
            r"^\s*(?P<header>[\S\s]*)\s*```latex\s*(?P<content>[\S\s]*)\s*```\s*$",
            src,
        )

        header: str = src_match.group("header").strip().replace("::", ":")
        content: str = src_match.group("content").strip()

        meta: dict = load_yaml(header)

        bit_model = BitModel(src=content, **meta)

        return bit_model

    def parse(self, path: Path) -> RegistryDataModel:
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()

        delimiter = "---"
        parts = content.split(delimiter)
        if len(parts) < 3:
            raise ValueError("Invalid frontmatter format")

        frontmatter_content = load_yaml(parts[1])
        targets: List[TargetModel] = [
            TargetModel(**target) for target in frontmatter_content["targets"]
        ]

        bits_src = filter(lambda x: x.strip(), parts[2:])
        bits: List[BitModel] = [self._parse_bit(bit_src) for bit_src in bits_src]

        return RegistryDataModel(bits=bits, targets=targets)


class RegistryFileYamlParser(RegistryFileParser):
    def parse(self, path: Path) -> RegistryDataModel:
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()

        data = load_yaml(content)

        bits: List[BitModel] = (
            [BitModel(**bit) for bit in data["bits"]] if "bits" in data else []
        )
        targets: List[TargetModel] = (
            [TargetModel(**target) for target in data["targets"]]
            if "targets" in data
            else []
        )

        return RegistryDataModel(bits=bits, targets=targets)
