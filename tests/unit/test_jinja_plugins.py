from pathlib import Path

from bits.env import EnvironmentFactory
from bits.config import config


def _set_plugins(paths):
    if not config.has_section("jinja"):
        config.add_section("jinja")
    config.set("jinja", "plugins", ",".join(str(p) for p in paths))
    # Ensure a fresh env cache per plugin configuration
    EnvironmentFactory._env_cache.clear()  # pylint: disable=protected-access


def test_jinja_plugin_loads_and_filter_works():
    plugin = Path("tests/resources/plugins/math_filters.py").resolve()
    _set_plugins([plugin])
    EnvironmentFactory.enable_plugins(True)

    env = EnvironmentFactory.get()
    assert "double" in env.filters
    assert env.filters["double"](3) == 6


def test_jinja_plugin_override_filter():
    plugin = Path("tests/resources/plugins/override_filters.py").resolve()
    _set_plugins([plugin])
    EnvironmentFactory.enable_plugins(True)

    env = EnvironmentFactory.get()
    assert "pick" in env.filters
    # The override returns a sentinel regardless of input
    assert env.filters["pick"]([1, 2, 3], [1]) == ["OVERRIDE"]


def test_jinja_plugin_missing_file_is_ignored():
    missing = Path("tests/resources/plugins/_missing.py").resolve()
    _set_plugins([missing])
    EnvironmentFactory.enable_plugins(True)

    env = EnvironmentFactory.get()
    # Missing plugin should not raise, and built-ins still available
    assert "pick" in env.filters
