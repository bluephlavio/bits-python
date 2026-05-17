"""Unit tests for target outputs feature (targets.outputs rendering variants)."""

from pathlib import Path

import pytest

from bits.models.target_model import TargetModel, TargetOutputModel
from bits.registry import RegistryFactory
from bits.registry.registryfile import RegistryFile


FIXTURE = Path("tests/resources/targets-outputs.yaml").resolve()


def _get_target(name: str):
    reg: RegistryFile = RegistryFactory.get(FIXTURE)
    for t in reg.targets:
        if t.name == name:
            return t
    raise AssertionError(f"Target not found: {name}")


# ---------------------------------------------------------------------------
# 1. Legacy target without outputs
# ---------------------------------------------------------------------------


def test_legacy_target_has_no_outputs():
    tgt = _get_target("no-outputs")
    assert tgt._outputs == []


def test_legacy_target_renders_normally():
    tgt = _get_target("no-outputs")
    tex = tgt.render_tex_code()
    assert "No Outputs Legacy" in tex


# ---------------------------------------------------------------------------
# 2. Target with outputs — implicit default (first output)
# ---------------------------------------------------------------------------


def test_multi_output_has_two_outputs():
    tgt = _get_target("multi-output")
    assert len(tgt._outputs) == 2
    assert tgt._outputs[0]["name"] == "student"
    assert tgt._outputs[1]["name"] == "key"


def test_multi_output_default_is_first():
    tgt = _get_target("multi-output")
    default = tgt._get_default_output()
    assert default is not None
    assert default["name"] == "student"


def test_multi_output_render_tex_code_uses_base():
    """render_tex_code() always returns base template for backward compat."""
    tgt = _get_target("multi-output")
    tex = tgt.render_tex_code()
    # Base template is outputs-student.tex.j2 which prints render_mode or "student"
    assert "student" in tex


# ---------------------------------------------------------------------------
# 3. Explicit default output
# ---------------------------------------------------------------------------


def test_explicit_default_output_is_key():
    tgt = _get_target("default-explicit")
    default = tgt._get_default_output()
    assert default is not None
    assert default["name"] == "key"


# ---------------------------------------------------------------------------
# 4. get_output lookup
# ---------------------------------------------------------------------------


def test_get_output_returns_correct_spec():
    tgt = _get_target("multi-output")
    out = tgt.get_output("key")
    assert out is not None
    assert out["name"] == "key"
    assert out["suffix"] == "key"


def test_get_output_missing_returns_none():
    tgt = _get_target("multi-output")
    assert tgt.get_output("nonexistent") is None


# ---------------------------------------------------------------------------
# 5 & 6. Dest computation
# ---------------------------------------------------------------------------


def test_output_dest_with_suffix():
    tgt = _get_target("multi-output")
    out = tgt.get_output("key")
    dest = tgt._compute_output_dest(out)
    assert dest.stem.endswith("-key")
    assert dest.suffix == ".pdf"
    assert dest.name == "multi-output-key.pdf"


def test_output_dest_without_suffix():
    tgt = _get_target("multi-output")
    out = tgt.get_output("student")
    dest = tgt._compute_output_dest(out)
    assert dest == tgt.dest
    assert dest.name == "multi-output.pdf"


# ---------------------------------------------------------------------------
# 7. Context overlay
# ---------------------------------------------------------------------------


def test_output_context_overlay():
    tgt = _get_target("multi-output")
    out = tgt.get_output("key")
    assert out["context"].get("render_mode") == "key"
    assert out["context"].get("title") == "Output Test"


def test_student_output_has_no_render_mode():
    tgt = _get_target("multi-output")
    out = tgt.get_output("student")
    assert "render_mode" not in out["context"]


# ---------------------------------------------------------------------------
# 8. Context overlay deep merge
# ---------------------------------------------------------------------------


def test_output_context_deep_merge():
    tgt = _get_target("deep-merge-output")
    out = tgt.get_output("variant")
    assert out is not None
    nested = out["context"]["nested"]
    # base_key preserved from parent context
    assert nested["base_key"] == "base_value"
    # shared_key overridden by output context
    assert nested["shared_key"] == "from_output"
    # output_key added by output context
    assert nested["output_key"] == "output_value"


# ---------------------------------------------------------------------------
# 9. Validation: multiple defaults raise ValueError
# ---------------------------------------------------------------------------


def test_multiple_defaults_raises():
    with pytest.raises(ValueError, match="multiple outputs have default=True"):
        TargetModel(
            name="bad",
            outputs=[
                TargetOutputModel(name="a", default=True),
                TargetOutputModel(name="b", default=True),
            ],
        )


# ---------------------------------------------------------------------------
# 10. render() with unknown output_name raises ValueError
# ---------------------------------------------------------------------------


def test_render_unknown_output_name_raises(tmp_path):
    tgt = _get_target("multi-output")
    with pytest.raises(ValueError, match="not found"):
        tgt.render(tex=True, output_name="nonexistent")


# ---------------------------------------------------------------------------
# 11. render() with output_name on target without outputs raises ValueError
# ---------------------------------------------------------------------------


def test_render_output_name_on_no_outputs_raises(tmp_path):
    tgt = _get_target("no-outputs")
    with pytest.raises(ValueError, match="has no outputs defined"):
        tgt.render(tex=True, output_name="anything")


# ---------------------------------------------------------------------------
# 12. Tex rendering: all_outputs produces files for each output
# ---------------------------------------------------------------------------


def test_render_all_outputs_tex(tmp_path):
    tgt = _get_target("multi-output")
    tgt.render(tex=True, all_outputs=True)
    # student output: multi-output.tex
    student_tex = tgt.dest.with_suffix(".tex")
    # key output: multi-output-key.tex
    key_dest = tgt._compute_output_dest(tgt.get_output("key"))
    key_tex = key_dest.with_suffix(".tex")

    assert student_tex.exists(), f"Expected {student_tex} to exist"
    assert key_tex.exists(), f"Expected {key_tex} to exist"

    # Verify content differs per template
    student_content = student_tex.read_text()
    key_content = key_tex.read_text()
    assert "Answer Key" not in student_content
    assert "Answer Key" in key_content


def test_render_specific_output_tex(tmp_path):
    tgt = _get_target("multi-output")
    tgt.render(tex=True, output_name="key")
    key_dest = tgt._compute_output_dest(tgt.get_output("key"))
    key_tex = key_dest.with_suffix(".tex")
    assert key_tex.exists()
    assert "Answer Key" in key_tex.read_text()


def test_render_default_output_tex(tmp_path):
    tgt = _get_target("multi-output")
    tgt.render(tex=True)
    student_tex = tgt.dest.with_suffix(".tex")
    assert student_tex.exists()
    content = student_tex.read_text()
    # student template shows "student" mode, no "Answer Key"
    assert "Answer Key" not in content
