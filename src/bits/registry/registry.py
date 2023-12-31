from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..bit import Bit
from ..collections import Collection
from ..target import Target
from ..watcher import Watcher


class Registry(ABC):
    def __init__(self, path: Path):
        if not path.exists():
            raise FileNotFoundError

        self._path: Path = path

        self._watcher: Watcher = Watcher(self._path)
        self._watcher.add_listener(self.load)

        self._bits: Collection[Bit] = Collection(Bit)
        self._targets: Collection[Target] = Collection(Target)

    @property
    def bits(self) -> Collection[Bit]:
        return self._bits

    @property
    def targets(self) -> Collection[Target]:
        return self._targets

    @abstractmethod
    def load(self, as_dep: bool = False) -> None:
        pass

    def render(self) -> None:
        for target in self._targets:
            target.render()

    def watch(self) -> None:
        self._watcher.start()

    def stop(self) -> None:
        self._watcher.stop()
