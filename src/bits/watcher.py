from pathlib import Path
from typing import Callable, List

from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers import Observer


class Watcher(PatternMatchingEventHandler):
    def __init__(self, path: Path):
        super().__init__(patterns=[path.name if path.suffix == ".md" else "**/*.md"])

        if not path.exists():
            raise FileNotFoundError(f"Path {path} does not exist")

        if path.is_file() and path.suffix != ".md":
            raise ValueError(f"Path {path} is not a markdown file")

        self._path: Path = path
        self._dir: Path = self._path if self._path.is_dir() else self._path.parent

        self._observer: Observer = Observer()
        self._observer.schedule(self, self._dir, recursive=True)

        self._listeners: List[Callable[[FileSystemEvent]], None] = []

    def add_listener(self, on_event: Callable[[FileSystemEvent], None]) -> None:
        if on_event not in self._listeners:
            self._listeners.append(on_event)

    def remove_listener(self, on_event: Callable[[FileSystemEvent], None]) -> None:
        try:
            self._listeners.remove(on_event)
        except ValueError:
            pass

    def on_any_event(self, event: FileSystemEvent):
        listener: Callable[[FileSystemEvent], None]
        for listener in self._listeners:
            listener(event)

    def start(self) -> None:
        self._observer.start()

    def stop(self) -> None:
        self._observer.stop()
        self._observer.join()
