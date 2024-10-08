from __future__ import annotations

from pathlib import Path
from typing import Callable

from .registry import Registry
from .registry_factory import RegistryFactory


class RegistryFolder(Registry):
    def __init__(self, path: Path, as_dep: bool = False):
        super().__init__(path)

        if not self._path.is_dir():
            raise NotADirectoryError

        self.load(as_dep=as_dep)

    def load(self, as_dep: bool = False) -> None:
        with self._load_lock:
            self._bits.clear()
            self._constants.clear()
            self._targets.clear()
            self._deps.clear()

            for path in self._path.rglob("**/*"):
                if path.suffix in {".md", ".yaml", ".yml"}:
                    registry: Registry = RegistryFactory.get(path, as_dep=as_dep)
                    self._bits.extend(registry.bits)
                    self._constants.extend(registry.constants)
                    self._targets.extend(registry.targets)
                    self.add_dep(registry)

    def add_listener(self, on_event: Callable, recursive=True) -> None:
        for dep in self._deps:
            dep.add_listener(on_event, recursive=recursive)

    def watch(self, recursive=True) -> None:
        for dep in self._deps:
            dep.watch(recursive=recursive)

    def stop(self, recursive=True) -> None:
        for dep in self._deps:
            dep.stop(recursive=recursive)
