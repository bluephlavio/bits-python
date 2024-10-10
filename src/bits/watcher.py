import time
from pathlib import Path
from threading import Timer
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
        self._last_modified = 0
        self._debounce_timer = None

    def add_listener(self, on_event: Callable[[FileSystemEvent], None]) -> None:
        if on_event not in self._listeners:
            self._listeners.append(on_event)

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.src_path == str(self._path):
            current_time = time.time()
            if current_time - self._last_modified < 1:  # Debounce interval of 1 second
                if self._debounce_timer:
                    self._debounce_timer.cancel()
                self._debounce_timer = Timer(1, self._notify_listeners, [event])
                self._debounce_timer.start()
            else:
                self._notify_listeners(event)
            self._last_modified = current_time

    def _notify_listeners(self, event: FileSystemEvent) -> None:
        try:
            for listener in self._listeners:
                listener(event)
        except Exception as e: # pylint: disable=broad-except
            print(f"Error while notifying listeners: {e}")

    def start(self) -> None:
        self._observer.start()

    def stop(self) -> None:
        self._observer.stop()
        self._observer.join()
