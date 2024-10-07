from pathlib import Path
from typing import Callable, List
from threading import Timer

from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers import Observer


class Watcher(PatternMatchingEventHandler):
    def __init__(self, path: Path):
        super().__init__(
            patterns=["*.md", "*.yaml", "*.yml", "**/*.md", "**/*.yaml", "**/*.yml"]
        )

        if not path.exists():
            raise FileNotFoundError(f"Path {path} does not exist")

        if path.is_file() and path.suffix not in [".md", ".yaml", ".yml"]:
            raise ValueError(f"Path {path} is not a markdown or yaml file")

        self._path: Path = path
        self._dir: Path = self._path if self._path.is_dir() else self._path.parent

        self._observer: Observer = Observer()
        self._observer.schedule(self, self._dir, recursive=True)

        self._listeners: List[Callable[[FileSystemEvent], None]] = []
        self._debounce_timer = None

    def add_listener(self, on_event: Callable[[FileSystemEvent], None]) -> None:
        if on_event not in self._listeners:
            self._listeners.append(on_event)

    def remove_listener(self, on_event: Callable[[FileSystemEvent], None]) -> None:
        try:
            self._listeners.remove(on_event)
        except ValueError:
            pass

    def on_any_event(self, event: FileSystemEvent):
        if event.is_directory:
            return
        if self._debounce_timer:
            self._debounce_timer.cancel()
        self._debounce_timer = Timer(0.1, self._notify_listeners, [event])
        self._debounce_timer.start()

    def _notify_listeners(self, event: FileSystemEvent):
        listener: Callable[[FileSystemEvent], None]
        for listener in self._listeners:
            listener(event)

    def start(self) -> None:
        self._observer.start()

    def stop(self) -> None:
        self._observer.stop()
        self._observer.join()
