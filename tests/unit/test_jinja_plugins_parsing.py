from pathlib import Path

from bits.config import config
from bits.env import EnvironmentFactory


def _set_plugins_raw(value: str) -> None:
    if not config.has_section("jinja"):
        config.add_section("jinja")
    config.set("jinja", "plugins", value)
    # Invalidate env cache to avoid cross-test leakage
    EnvironmentFactory._env_cache.clear()  # pylint: disable=protected-access


def _as_posix_list(paths):
    return [p.as_posix() for p in paths]


def test_plugins_parsing_single_string():
    path = "tests/resources/plugins/math_filters.py"
    _set_plugins_raw(path)
    plugins = EnvironmentFactory._get_plugins_list()  # pylint: disable=protected-access
    assert _as_posix_list(plugins) == [Path(path).expanduser().as_posix()]


def test_plugins_parsing_comma_separated():
    p1 = "tests/resources/plugins/math_filters.py"
    p2 = "tests/resources/plugins/override_filters.py"
    _set_plugins_raw(f"{p1}, {p2}")
    plugins = EnvironmentFactory._get_plugins_list()  # pylint: disable=protected-access
    assert _as_posix_list(plugins) == [
        Path(p1).expanduser().as_posix(),
        Path(p2).expanduser().as_posix(),
    ]


def test_plugins_parsing_newline_separated():
    p1 = "tests/resources/plugins/math_filters.py"
    p2 = "tests/resources/plugins/override_filters.py"
    # Simulate multi-line value as produced by configparser continuation lines
    _set_plugins_raw(f"\n    {p1}\n    {p2}\n")
    plugins = EnvironmentFactory._get_plugins_list()  # pylint: disable=protected-access
    assert _as_posix_list(plugins) == [
        Path(p1).expanduser().as_posix(),
        Path(p2).expanduser().as_posix(),
    ]


def test_plugins_parsing_list_literal():
    p1 = "tests/resources/plugins/math_filters.py"
    p2 = "tests/resources/plugins/override_filters.py"
    # Python/TOML-like array literal (valid as a single INI value)
    value = f"""[
        \"{p1}\",
        \"{p2}\",
    ]"""
    _set_plugins_raw(value)
    plugins = EnvironmentFactory._get_plugins_list()  # pylint: disable=protected-access
    assert _as_posix_list(plugins) == [
        Path(p1).expanduser().as_posix(),
        Path(p2).expanduser().as_posix(),
    ]

