from pathlib import Path
from typing import Callable, List

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class Watcher(FileSystemEventHandler):
    def __init__(self, path: Path):
        super().__init__()

        if not path.exists():
            raise FileNotFoundError(f"Path {path} does not exist")

        if not path.is_file() or path.suffix not in [".md", ".yaml", ".yml"]:
            raise ValueError(f"Path {path} is not a markdown or yaml file")

        self._path: Path = path

        self._observer: Observer = Observer()
        self._observer.schedule(self, str(self._path.parent), recursive=False)

        self._listeners: List[Callable[[FileSystemEvent], None]] = []

    def add_listener(self, on_event: Callable[[FileSystemEvent], None]) -> None:
        if on_event not in self._listeners:
            self._listeners.append(on_event)

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.src_path == str(self._path):
            for listener in self._listeners:
                listener(event)

    def start(self) -> None:
        self._observer.start()

    def stop(self) -> None:
        self._observer.stop()
        self._observer.join()
