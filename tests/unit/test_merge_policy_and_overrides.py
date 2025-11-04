from pathlib import Path

import pytest

from bits.registry import RegistryFactory


def render_tex(path: Path, target_name: str) -> str:
    reg = RegistryFactory.get(path)
    tgt = None
    for t in reg.targets:
        if t.name == target_name:
            tgt = t
            break
    assert tgt is not None, f"Target not found: {target_name}"
    return tgt.render_tex_code()


def test_target_merge_queries_replace():
    path = Path("tests/resources/targets-extends-merge-policy.yaml").resolve()
    tex = render_tex(path, "Derived Replace Queries")
    # Only Q3 should appear
    assert "Q3" in tex
    assert "Q1" not in tex and "Q2" not in tex


def test_target_merge_context_replace():
    path = Path("tests/resources/targets-extends-merge-policy.yaml").resolve()
    tex = render_tex(path, "Derived Replace Context")
    assert "New Title" in tex
    assert "Base Title" not in tex


def test_overrides_op_merge_deep_list_dicts():
    path = Path("tests/resources/targets-extends-merge-policy.yaml").resolve()
    tex = render_tex(path, "Derived Merge Override")
    # Expect first item: Q1 with original pts, second item changed to Q3 and pts partially overridden
    assert "Q1" in tex and "Q3" in tex
    # The metadata pts for second item should start with 9, 9 due to index-wise merge
    assert "[9, 9" in tex


def test_overrides_root_replace_queries():
    path = Path("tests/resources/targets-extends-merge-policy.yaml").resolve()
    tex = render_tex(path, "Derived Root Replace Queries")
    assert "Q4" in tex
    assert "Q1" not in tex and "Q2" not in tex


def test_preset_merge_queries_replace():
    path = Path("tests/resources/bits-presets-merge-policy.yaml").resolve()
    tex = render_tex(path, "Preset Merge Replace")
    # Should reference the G constant (not c), i.e., symbol $G$
    assert "$G$" in tex
    assert "$c$" not in tex

