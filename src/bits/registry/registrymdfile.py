import re
from typing import List

from ..yaml_loader import load_yaml
from ..bit import Bit
from ..models import TargetModel, BitModel
from ..target import Target
from .registryfile import RegistryFile


class RegistryMdFile(RegistryFile):
    def _check_file_type(self):
        if not self._path.suffix == ".md":
            raise ValueError("Expected a .md file")

    def load(self, as_dep: bool = False) -> None:
        with open(self._path, "r", encoding="utf-8") as file:
            content = file.read()

        delimiter = "---"
        parts = content.split(delimiter)
        if len(parts) < 3:
            raise ValueError("Invalid frontmatter format")

        frontmatter_content = parts[1]
        post_content = delimiter.join(parts[2:])

        post_metadata = load_yaml(frontmatter_content)

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

    def _parse_bit(self, src: str) -> Bit:
        src_match: re.Match = re.match(
            r"^\s*(?P<header>[\S\s]*)\s*```latex\s*(?P<content>[\S\s]*)\s*```\s*$",
            src,
        )

        header: str = src_match.group("header").strip().replace("::", ":")
        content: str = src_match.group("content").strip()

        meta: dict = load_yaml(header)

        bit_model = BitModel(src=content, **meta)

        bit: Bit = Bit(bit_model.src, **bit_model.metadata)
        return bit
