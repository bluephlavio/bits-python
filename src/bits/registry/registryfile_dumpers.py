from abc import ABC, abstractmethod
from pathlib import Path

import yaml

from ..models import BitModel, RegistryDataModel


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
        header = yaml.dump(filtered_bit, default_flow_style=False).strip()
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
        frontmatter = yaml.dump(filtered_data, default_flow_style=False).strip()
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
        content = yaml.dump(filtered_data, default_flow_style=False, sort_keys=False)

        with open(path, "w", encoding="utf-8") as file:
            file.write(content)


class RegistryFileDumperFactory:
    @staticmethod
    def get(path: Path) -> RegistryFileDumper:
        if path.suffix in [".yml", ".yaml"]:
            return RegistryFileYamlDumper()
        if path.suffix == ".md":
            return RegistryFileMdDumper()
        raise ValueError(f"Unsupported file format: {path.suffix}")
