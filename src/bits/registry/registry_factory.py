# pylint: disable=import-outside-toplevel

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
            from .registryfile import RegistryFile

            registry = RegistryFile(normalized_path, **kwargs)
        elif normalized_path.is_dir():
            index_file = RegistryFactory.search_for_index(normalized_path)
            if index_file:
                from .registryfile import RegistryFile

                registry = RegistryFile(index_file, **kwargs)
            else:
                from .registryfolder import RegistryFolder

                registry = RegistryFolder(normalized_path, **kwargs)
        else:
            raise ValueError(f"Invalid path: {normalized_path}")

        registry.load(**kwargs)
        RegistryFactory._cache[normalized_path] = registry
        return registry

    @staticmethod
    def search_for_index(path: Path) -> Union[Path, None]:
        for index_file in ["index.md", "index.yaml", "index.yml"]:
            index_path = path / index_file
            if index_path.exists():
                return index_path
        return None
