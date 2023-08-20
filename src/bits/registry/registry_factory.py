from functools import lru_cache
from pathlib import Path

from ..helpers import normalize_path


class RegistryFactory:  # pylint: disable=too-few-public-methods
    @staticmethod
    @lru_cache(maxsize=None)
    def get(path: Path | str, **kwargs):
        normalized_path: Path = normalize_path(path)

        if normalized_path.is_file():
            from .registryfile import (  # pylint: disable=import-outside-toplevel
                RegistryFile,
            )

            return RegistryFile(normalized_path, **kwargs)

        if normalized_path.is_dir():
            from .registryfolder import (  # pylint: disable=import-outside-toplevel
                RegistryFolder,
            )

            return RegistryFolder(normalized_path, **kwargs)

        raise FileNotFoundError("Invalid registry path")
