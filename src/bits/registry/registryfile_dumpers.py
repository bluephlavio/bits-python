from abc import ABC, abstractmethod
from pathlib import Path
import yaml

from ..models import RegistryDataModel, BitModel


class RegistryFileDumper(ABC):
    @abstractmethod
    def dump(self, data: RegistryDataModel, path: Path) -> None:
        pass


class RegistryFileMdDumper(RegistryFileDumper):
    def _dump_bit(self, bit: BitModel) -> str:
        header = yaml.dump(bit.dict(exclude={"src"}), default_flow_style=False).strip()
        content = bit.src.strip()
        return f"{header}\n```latex\n{content}\n```"

    def dump(self, data: RegistryDataModel, path: Path) -> None:
        if not path.suffix == ".md":
            raise ValueError(f"Unsupported file format: {path.suffix}")

        frontmatter = yaml.dump(
            {
                "targets": [target.dict() for target in data.targets],
                "constants": [constant.dict() for constant in data.constants],
            },
            default_flow_style=False,
        ).strip()
        bits_content = "\n---\n".join(self._dump_bit(bit) for bit in data.bits)

        content = f"---\n{frontmatter}\n---\n{bits_content}"

        with open(path, "w", encoding="utf-8") as file:
            file.write(content)


class RegistryFileYamlDumper(RegistryFileDumper):
    def dump(self, data: RegistryDataModel, path: Path) -> None:
        if not path.suffix in [".yml", ".yaml"]:
            raise ValueError(f"Unsupported file format: {path.suffix}")

        content = yaml.dump(data.dict(), default_flow_style=False)

        with open(path, "w", encoding="utf-8") as file:
            file.write(content)


class RegistryFileDumperFactory:
    @staticmethod
    def get(path: Path) -> RegistryFileDumper:
        if path.suffix in [".yml", ".yaml"]:
            return RegistryFileYamlDumper()
        elif path.suffix == ".md":
            return RegistryFileMdDumper()
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
