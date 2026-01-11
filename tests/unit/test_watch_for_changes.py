from types import SimpleNamespace

from bits.cli.helpers import watch_for_changes


class DummyRegistry:
    def __init__(self) -> None:
        self.listener = None
        self.load_calls = []
        self.render_calls = []
        self.watch_calls = []

    def add_listener(self, on_event, recursive=True) -> None:
        self.listener = on_event

    def watch(self, recursive=True) -> None:
        self.watch_calls.append(recursive)

    def stop(self, recursive=True) -> None:
        return None

    def load(self, as_dep=False) -> None:
        self.load_calls.append(as_dep)

    def render(self, **kwargs) -> None:
        self.render_calls.append(kwargs)


class DummyConsole:
    def print(self, *args, **kwargs) -> None:
        return None

    def rule(self, *args, **kwargs) -> None:
        return None


def test_watch_for_changes_rerender_uses_render_options(tmp_path):
    registry = DummyRegistry()
    console = DummyConsole()
    build_dir = tmp_path / "build"
    intermediates_dir = tmp_path / "intermediates"

    watch_for_changes(
        registry,
        console,
        output_tex=True,
        pdf=True,
        tex=False,
        both=False,
        build_dir=build_dir,
        intermediates_dir=intermediates_dir,
        keep_intermediates="errors",
        unique_strategy="uuid",
        loop=False,
    )

    assert registry.listener is not None
    registry.listener(SimpleNamespace(src_path="bits.yml"))

    assert registry.load_calls == [False]
    assert len(registry.render_calls) == 1
    kwargs = registry.render_calls[0]
    assert kwargs["output_tex"] is True
    assert kwargs["pdf"] is True
    assert kwargs["tex"] is False
    assert kwargs["both"] is False
    assert kwargs["build_dir"] == build_dir
    assert kwargs["intermediates_dir"] == intermediates_dir
    assert kwargs["keep_intermediates"] == "errors"
    assert kwargs["unique_strategy"] == "uuid"


def test_watch_for_changes_ignores_irrelevant_files(tmp_path):
    registry = DummyRegistry()
    console = DummyConsole()

    watch_for_changes(
        registry,
        console,
        output_tex=False,
        build_dir=tmp_path / "build",
        loop=False,
    )

    assert registry.listener is not None
    registry.listener(SimpleNamespace(src_path="notes.txt"))

    assert registry.load_calls == []
    assert registry.render_calls == []
