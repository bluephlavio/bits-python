from abc import ABC, abstractmethod
from pathlib import Path

import yaml

from ..models import BitModel, RegistryDataModel


class BitsYamlDumper(yaml.Dumper):
    def represent_data(self, data):
        if isinstance(data, dict):
            node = super().represent_data(data)

            for key_node, value_node in node.value:
                if key_node.value == "tags" and isinstance(
                    value_node, yaml.SequenceNode
                ):
                    value_node.flow_style = True

                if key_node.value == "src" and isinstance(value_node, yaml.ScalarNode):
                    value_node.style = "|"

            return node
        return super().represent_data(data)


class RegistryFileDumper(ABC):
    @abstractmethod
    def dump(self, data: RegistryDataModel, path: Path) -> None:
        pass


class RegistryFileMdDumper(RegistryFileDumper):
    def _dump_bit(self, bit: BitModel) -> str:
        filtered_bit = {
            k: v
            for k, v in bit.dict(exclude={"src"}).items()
            if v not in [None, [], {}]
        }
        header = yaml.dump(
            filtered_bit, default_flow_style=False, sort_keys=False
        ).strip()
        content = bit.src.strip()
        return f"{header}\n```latex\n{content}\n```"

    def dump(self, data: RegistryDataModel, path: Path) -> None:
        if not path.suffix == ".md":
            raise ValueError(f"Unsupported file format: {path.suffix}")

        filtered_data = {
            k: v
            for k, v in {
                "tags": data.tags,
                "targets": [target.dict() for target in data.targets],
                "constants": [constant.dict() for constant in data.constants],
                "import": list(data.imports),
            }.items()
            if v not in [None, [], {}]
        }
        frontmatter = yaml.dump(
            filtered_data, default_flow_style=False, sort_keys=False
        ).strip()
        bits_content = "\n---\n".join(self._dump_bit(bit) for bit in data.bits)

        content = f"---\n{frontmatter}\n---\n{bits_content}"

        with open(path, "w", encoding="utf-8") as file:
            file.write(content)


class RegistryFileYamlDumper(RegistryFileDumper):
    def dump(self, data: RegistryDataModel, path: Path) -> None:
        if not path.suffix in [".yml", ".yaml"]:
            raise ValueError(f"Unsupported file format: {path.suffix}")

        filtered_data = {
            k: v for k, v in data.dict().items() if v not in [None, [], {}]
        }
        filtered_data["bits"] = [
            {k: v for k, v in bit.items() if v not in [None, [], {}]}
            for bit in filtered_data["bits"]
        ]

        with open(path, "w", encoding="utf-8") as file:
            yaml.dump(
                filtered_data,
                file,
                Dumper=BitsYamlDumper,
                default_flow_style=False,
                sort_keys=False,
            )


class RegistryFileDumperFactory:
    @staticmethod
    def get(path: Path) -> RegistryFileDumper:
        if path.suffix in [".yml", ".yaml"]:
            return RegistryFileYamlDumper()
        if path.suffix == ".md":
            return RegistryFileMdDumper()
        raise ValueError(f"Unsupported file format: {path.suffix}")
