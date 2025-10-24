from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, List

from ..bit import Bit
from ..collections import Collection
from ..constant import Constant
from ..target import Target


class Registry(ABC):
    def __init__(self, path: Path):
        if not path.exists():
            raise FileNotFoundError

        self._path: Path = path

        self._deps: List[Registry] = []

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

    def clear_registry(self) -> None:
        self._bits.clear()
        self._constants.clear()
        self._targets.clear()
        self._deps.clear()

    def render(
        self,
        output_tex: bool = False,
        *,
        pdf: bool | None = None,
        tex: bool | None = None,
        both: bool = False,
        build_dir=None,
        intermediates_dir=None,
        keep_intermediates: str = "none",
        unique_strategy: str | None = None,
    ) -> None:
        with self._load_lock:
            for target in self._targets:
                target.render(
                    output_tex=output_tex,
                    pdf=pdf,
                    tex=tex,
                    both=both,
                    build_dir=build_dir,
                    intermediates_dir=intermediates_dir,
                    keep_intermediates=keep_intermediates,
                    unique_strategy=unique_strategy,
                )

    def add_dep(self, registry: Registry) -> None:
        if not isinstance(registry, Registry):
            raise TypeError(f"Expected Registry, got {type(registry)}")
        if registry not in self._deps:
            self._deps.append(registry)

    @abstractmethod
    def add_listener(self, on_event: Callable, recursive=True) -> None:
        pass

    @abstractmethod
    def watch(self, recursive=True) -> None:
        pass

    @abstractmethod
    def stop(self, recursive=True) -> None:
        pass
