# pylint: disable=protected-access
from pathlib import Path

import pytest

from bits.bit import Bit
from bits.config import config
from bits.dialects import DialectRegistry
from bits.exceptions import DialectError


@pytest.fixture(autouse=True)
def isolated_dialect_config():
    original = None
    if config.has_section("dialects"):
        original = dict(config._sections["dialects"])
        original.pop("__name__", None)
        config.remove_section("dialects")
    DialectRegistry.clear_cache()

    yield

    if config.has_section("dialects"):
        config.remove_section("dialects")
    if original is not None:
        config.add_section("dialects")
        for key, value in original.items():
            config.set("dialects", key, value)
    DialectRegistry.clear_cache()


def _write_plugin(tmp_path: Path, body: str, name: str = "dialect.py") -> Path:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


def _set_dialect(name: str, path: Path, function: str = "transform") -> None:
    if not config.has_section("dialects"):
        config.add_section("dialects")
    config.set("dialects", name, f"{path.as_posix()}:{function}")
    DialectRegistry.clear_cache()


def test_bit_without_dialect_renders_as_before():
    bit = Bit(src=r"Hello \VAR{ name }")

    assert bit.render(name="Ada") == "Hello Ada"


def test_bit_with_configured_dialect_transforms_before_jinja(tmp_path):
    plugin = _write_plugin(
        tmp_path,
        r"""
def transform(source, **kwargs):
    assert kwargs["metadata"]["name"] == "Greeting"
    assert kwargs["context"]["name"] == "Ada"
    return source.replace("@name", r"\VAR{ name }")
""",
    )
    _set_dialect("testdialect", plugin)

    bit = Bit(src="Hello @name", name="Greeting", dialect="testdialect")

    assert bit.render(name="Ada") == "Hello Ada"


def test_dialect_can_emit_jinja_source(tmp_path):
    plugin = _write_plugin(
        tmp_path,
        r"""
def transform(source):
    return source.replace(
        "@visible",
        r"\BLOCK{ if show }visible\BLOCK{ endif }",
    )
""",
    )
    _set_dialect("testdialect", plugin)

    bit = Bit(src="@visible", dialect="testdialect")

    assert bit.render(show=True) == "visible"
    assert bit.render(show=False) == ""


def test_multi_fragment_bit_transforms_each_fragment(tmp_path):
    plugin = _write_plugin(
        tmp_path,
        r"""
def transform(source, **kwargs):
    return source.replace("@name", r"\VAR{ name }")
""",
    )
    _set_dialect("testdialect", plugin)

    bit = Bit(
        src={
            "default": "Question for @name",
            "solution": "Solution for @name",
        },
        dialect="testdialect",
    )

    assert bit.render(name="Ada") == "Question for Ada"
    assert bit.render("solution", name="Ada") == "Solution for Ada"


def test_unknown_dialect_produces_clear_error():
    bit = Bit(src="Hello", dialect="missing")

    with pytest.raises(DialectError, match="Unknown dialect 'missing'") as exc:
        bit.render()

    assert "Configure it under [dialects]" in str(exc.value)


def test_transform_exception_is_wrapped_as_dialect_error(tmp_path):
    plugin = _write_plugin(
        tmp_path,
        """
def transform(source, **kwargs):
    raise ValueError("boom")
""",
    )
    _set_dialect("testdialect", plugin)

    bit = Bit(
        src="Hello",
        dialect="testdialect",
        source_path="collections/example.yml",
    )

    with pytest.raises(DialectError) as exc:
        bit.render()

    assert "Dialect transform failed: boom" in str(exc.value)
    assert "testdialect" in str(exc.value)
    assert "collections/example.yml" in str(exc.value)
    assert isinstance(exc.value.__cause__, ValueError)


def test_workspace_raised_dialect_error_is_preserved(tmp_path):
    plugin = _write_plugin(
        tmp_path,
        """
from bits.exceptions import DialectError

def transform(source, **kwargs):
    raise DialectError(
        "bad authoring",
        dialect="testdialect",
        line=3,
        source_path=kwargs.get("path"),
    )
""",
    )
    _set_dialect("testdialect", plugin)

    bit = Bit(
        src="Hello",
        dialect="testdialect",
        source_path="collections/example.yml",
    )

    with pytest.raises(DialectError) as exc:
        bit.render()

    assert "Dialect transform failed" not in str(exc.value)
    assert "bad authoring" in str(exc.value)
    assert "line 3" in str(exc.value)
    assert exc.value.__cause__ is None


def test_bit_model_stores_dialect():
    bit = Bit(src="Hello", dialect="testdialect")

    assert bit.dialect == "testdialect"
    assert bit.to_model().dialect == "testdialect"
