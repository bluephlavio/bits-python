from pathlib import Path
from typing import Union

from ..helpers import normalize_path
from .registry import Registry


class RegistryFactory:  # pylint: disable=too-few-public-methods
    _cache = {}

    @staticmethod
    def get(path: Union[Path, str], **kwargs) -> Registry:
        normalized_path: Path = normalize_path(path)

        if normalized_path in RegistryFactory._cache:
            registry: Registry = RegistryFactory._cache[normalized_path]
            registry.load(**kwargs)
            return registry

        if normalized_path.is_file():
            # pylint: disable=import-outside-toplevel
            from .registryfile import RegistryFile

            registry = RegistryFile(normalized_path, **kwargs)
        elif normalized_path.is_dir():
            # pylint: disable=import-outside-toplevel
            from .registryfolder import RegistryFolder

            registry = RegistryFolder(normalized_path, **kwargs)
        else:
            raise ValueError(f"Invalid path: {normalized_path}")

        registry.load(**kwargs)
        RegistryFactory._cache[normalized_path] = registry
        return registry
