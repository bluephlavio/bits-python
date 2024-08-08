from functools import lru_cache
from pathlib import Path

from ..helpers import normalize_path


class RegistryFactory:  # pylint: disable=too-few-public-methods
    @staticmethod
    @lru_cache(maxsize=None)
    def get(path: Path | str, **kwargs):
        normalized_path: Path = normalize_path(path)

        if normalized_path.is_file():
            if normalized_path.suffix == ".md":
                from .registrymdfile import (
                    RegistryMdFile,
                )  # pylint: disable=import-outside-toplevel

                return RegistryMdFile(normalized_path, **kwargs)
            elif normalized_path.suffix in [".yaml", ".yml"]:
                from .registryyamlfile import (
                    RegistryYamlFile,
                )  # pylint: disable=import-outside-toplevel

                return RegistryYamlFile(normalized_path, **kwargs)
            raise ValueError("Unsupported file type")

        if normalized_path.is_dir():
            from .registryfolder import (
                RegistryFolder,
            )  # pylint: disable=import-outside-toplevel

            return RegistryFolder(normalized_path, **kwargs)
