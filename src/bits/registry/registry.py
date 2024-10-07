from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
import threading

from ..bit import Bit
from ..collections import Collection
from ..constant import Constant
from ..target import Target
from ..watcher import Watcher


class Registry(ABC):
    def __init__(self, path: Path):
        if not path.exists():
            raise FileNotFoundError

        self._path: Path = path

        self._deps: List[Registry] = []

        self._watcher: Watcher = Watcher(self._path)

        self._bits: Collection[Bit] = Collection(Bit)
        self._constants: Collection[Constant] = Collection(Constant)
        self._targets: Collection[Target] = Collection(Target)

        self._load_lock = threading.Lock()

    @property
    def deps(self) -> List[Registry]:
        return self._deps

    @property
    def bits(self) -> Collection[Bit]:
        return self._bits

    @property
    def constants(self) -> Collection[Constant]:
        return self._constants

    @property
    def targets(self) -> Collection[Target]:
        return self._targets

    @abstractmethod
    def load(self, as_dep: bool = False) -> None:
        pass

    def render(self) -> None:
        with self._load_lock:
            for target in self._targets:
                target.render()

    def add_dep(self, registry: Registry) -> None:
        if not isinstance(registry, Registry):
            raise TypeError(f"Expected Registry, got {type(registry)}")
        if registry not in self._deps:
            self._deps.append(registry)

    def add_listener(self, on_event, recursive=True) -> None:
        self._watcher.add_listener(on_event)
        if recursive:
            for dep in self._deps:
                dep.add_listener(on_event, recursive=True)

    def watch(self) -> None:
        self._watcher.start()

    def stop(self) -> None:
        self._watcher.stop()
