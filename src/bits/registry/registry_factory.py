# pylint: disable=import-outside-toplevel

from pathlib import Path
from typing import Union

from ..exceptions import RegistryNotFoundError
from ..helpers import normalize_path
from .registry import Registry


class RegistryFactory:  # pylint: disable=too-few-public-methods
    _cache = {}

    @staticmethod
    def get(path: Union[Path, str], **kwargs) -> Registry:
        normalized_path: Path = normalize_path(path)

        if normalized_path in RegistryFactory._cache:
            registry: Registry = RegistryFactory._cache[normalized_path]
            # Ensure cache entry is reloaded with potentially new kwargs
            registry.load(**kwargs)
            return registry

        registry_path_to_load = normalized_path
        if normalized_path.is_dir():
            index_file = RegistryFactory.search_for_index(normalized_path)
            if index_file:
                registry_path_to_load = index_file
            else:
                # If it's a directory without an index file, raise error.
                raise RegistryNotFoundError(
                    path=normalized_path,
                    message=f"Directory '{normalized_path}' is not a valid registry. No index file (index.md, index.yaml, index.yml) found.",
                )
        elif not normalized_path.is_file():
            # If it's not a file and not a directory (or doesn't exist)
            raise RegistryNotFoundError(path=normalized_path)

        # At this point, registry_path_to_load should be a file (either the original path or an index file)
        from .registryfile import RegistryFile

        registry = RegistryFile(registry_path_to_load, **kwargs)

        registry.load(**kwargs)
        # Cache based on the original normalized path requested
        RegistryFactory._cache[normalized_path] = registry
        return registry

    @staticmethod
    def search_for_index(path: Path) -> Union[Path, None]:
        for index_file in ["index.md", "index.yaml", "index.yml"]:
            index_path = path / index_file
            if index_path.exists():
                return index_path
        return None
