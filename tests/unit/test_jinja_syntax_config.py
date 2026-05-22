# pylint: disable=protected-access
import pytest

from bits.config import config
from bits.env import EnvironmentFactory


@pytest.fixture(autouse=True)
def isolated_jinja_syntax_config():
    plugins_enabled = EnvironmentFactory._plugins_enabled
    if config.has_section("jinja.syntax"):
        config.remove_section("jinja.syntax")
    EnvironmentFactory._env_cache.clear()
    EnvironmentFactory.enable_plugins(False)

    yield

    if config.has_section("jinja.syntax"):
        config.remove_section("jinja.syntax")
    EnvironmentFactory._env_cache.clear()
    EnvironmentFactory.enable_plugins(plugins_enabled)


def _set_syntax(**options):
    if not config.has_section("jinja.syntax"):
        config.add_section("jinja.syntax")
    for key, value in options.items():
        if isinstance(value, bool):
            value = "true" if value else "false"
        config.set("jinja.syntax", key, str(value))


def test_default_syntax_supports_latex_delimiters_and_line_statements():
    env = EnvironmentFactory.get()
    template = env.from_string(
        "Hello \\VAR{ name }\n" "%% if show\n" "visible\n" "%% endif\n"
    )

    rendered = template.render(name="Ada", show=True)

    assert "Hello Ada" in rendered
    assert "visible" in rendered


def test_custom_variable_delimiters_work():
    _set_syntax(
        variable_start_string="{{",
        variable_end_string="}}",
        trim_blocks=False,
        lstrip_blocks=True,
        autoescape=True,
    )

    env = EnvironmentFactory.get()
    rendered = env.from_string("Hello {{ name }} (\\VAR{ name })").render(name="Ada")

    assert rendered == "Hello Ada (\\VAR{ name })"
    assert env.trim_blocks is False
    assert env.lstrip_blocks is True
    assert env.autoescape is True


def test_custom_block_delimiters_work():
    _set_syntax(
        block_start_string="{%",
        block_end_string="%}",
    )

    env = EnvironmentFactory.get()
    template = env.from_string("{% if show %}shown{% else %}hidden{% endif %}")

    assert template.render(show=True) == "shown"
    assert template.render(show=False) == "hidden"


def test_syntax_options_separate_cached_environments():
    _set_syntax(
        variable_start_string="{{",
        variable_end_string="}}",
    )
    first = EnvironmentFactory.get()

    assert EnvironmentFactory.get() is first

    _set_syntax(
        variable_start_string="[[",
        variable_end_string="]]",
    )
    second = EnvironmentFactory.get()

    assert second is not first
    assert second.from_string("[[ name ]] {{ name }}").render(name="Ada") == (
        "Ada {{ name }}"
    )


def test_unknown_and_malformed_syntax_options_do_not_break_rendering():
    _set_syntax(
        unknown_option="ignored",
        trim_blocks="sometimes",
    )

    with pytest.warns(UserWarning, match="Invalid boolean.*trim_blocks"):
        env = EnvironmentFactory.get()

    rendered = env.from_string("\\VAR{ name }").render(name="Ada")

    assert rendered == "Ada"
    assert env.trim_blocks is True
