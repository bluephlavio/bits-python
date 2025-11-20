from pathlib import Path

from bits.config import config
from bits.env import EnvironmentFactory


def _ensure_jinja_section():
    if not config.has_section("jinja"):
        config.add_section("jinja")


def _set_jinja_option(key: str, value: str) -> None:
    _ensure_jinja_section()
    config.set("jinja", key, value)
    # Invalidate env cache so each config takes effect
    EnvironmentFactory._env_cache.clear()  # pylint: disable=protected-access


def test_auto_filter_files_register_functions_as_filters():
    path = Path("tests/resources/plugins/auto_filters.py").resolve()
    _set_jinja_option("filter_files", str(path))
    EnvironmentFactory.enable_plugins(True)

    env = EnvironmentFactory.get()
    assert "double" in env.filters
    assert env.filters["double"](3) == 6
    assert "add" in env.filters
    assert env.filters["add"](2, 5) == 7
    # helper is not a callable; must not be registered
    assert "helper" not in env.filters


def test_auto_filter_files_trim_suffix_for_common_pattern():
    path = Path("tests/resources/plugins/auto_filters_suffix.py").resolve()
    _set_jinja_option("filter_files", str(path))
    EnvironmentFactory.enable_plugins(True)

    env = EnvironmentFactory.get()
    # Functions named "<name>_filter" should be exposed as "<name>"
    assert "floor" in env.filters
    assert env.filters["floor"](3.7) == 3
    assert "ceil" in env.filters
    assert env.filters["ceil"](3.1) == 4


def test_auto_macro_files_register_macros_as_globals():
    macro_path = Path("tests/resources/templates/macros_auto.tex.j2").resolve()
    _set_jinja_option("macro_files", str(macro_path))
    EnvironmentFactory.enable_plugins(True)

    env = EnvironmentFactory.get()
    # Macro should be available as a global callable
    tpl = env.from_string(r"\VAR{ render_test(7) }")
    out = tpl.render()
    assert "Value: 7" in out


def test_macros_can_use_custom_filters_from_filter_files():
    filt_path = Path(
        "tests/resources/plugins/auto_filters_for_macros.py"
    ).resolve()
    macro_path = Path(
        "tests/resources/templates/macros_with_filter.tex.j2"
    ).resolve()
    _set_jinja_option("filter_files", str(filt_path))
    _set_jinja_option("macro_files", str(macro_path))
    EnvironmentFactory.enable_plugins(True)

    env = EnvironmentFactory.get()
    tpl = env.from_string(r"\VAR{ render_with_double(5) }")
    out = tpl.render()
    assert "Value: 10" in out
