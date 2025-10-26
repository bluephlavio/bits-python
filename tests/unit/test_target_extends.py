from pathlib import Path
import pytest

from bits.registry import RegistryFactory
from bits.registry.registryfile import RegistryFile
from bits.exceptions import RegistryReferenceError, RegistryLoadError


def render_tex(path: Path, target_name: str) -> str:
    reg: RegistryFile = RegistryFactory.get(path)
    tgt = None
    for t in reg.targets:
        if t.name == target_name:
            tgt = t
            break
    assert tgt is not None, f"Target not found: {target_name}"
    return tgt.render_tex_code()


def test_multi_extends_merges_and_overrides():
    path = Path("tests/resources/targets-extends.yaml").resolve()
    tex = render_tex(path, "Base Test — BES")
    # Title contains suffix from profile
    assert "\\section*{Base — BES}" in tex or "Base — BES" in tex
    # blocks order: Q1 then Q3 (override changed second from Q2 to Q3)
    assert tex.find("Q1") != -1
    assert tex.find("Q3") != -1
    assert tex.find("Q1") < tex.find("Q3")
    assert "Q2" not in tex


def test_overrides_only_changes_queries():
    path = Path("tests/resources/targets-extends.yaml").resolve()
    tex = render_tex(path, "Overrides Only")
    # New order: Q4 then Q3
    assert tex.find("Q4") != -1 and tex.find("Q3") != -1
    assert tex.find("Q4") < tex.find("Q3")


def test_compose_override_interleave_changes_order():
    path = Path("tests/resources/targets-extends.yaml").resolve()
    tex = render_tex(path, "Compose Derived Interleave")
    # Expected interleaved order: Q1, Q3, Q2, Q4
    i1 = tex.find("Q1")
    i2 = tex.find("Q3")
    i3 = tex.find("Q2")
    i4 = tex.find("Q4")
    assert -1 not in (i1, i2, i3, i4)
    assert i1 < i2 < i3 < i4


def test_cross_file_extends_resolves_and_applies():
    path = Path("tests/resources/targets-extends.yaml").resolve()
    tex = render_tex(path, "Base Test — DSA (XFile)")
    assert "Base — DSA" in tex
    # Q2 replaced with Q4 by cross-file profile
    assert tex.find("Q1") != -1 and tex.find("Q4") != -1
    assert tex.find("Q2") == -1


def test_missing_base_raises_reference_error():
    path = Path("tests/resources/invalid/targets-extends-missing.yaml").resolve()
    with pytest.raises(RegistryLoadError):
        RegistryFactory.get(path)


def test_cycle_detection_raises_reference_error():
    path = Path("tests/resources/invalid/targets-extends-cycle.yaml").resolve()
    with pytest.raises(RegistryLoadError):
        RegistryFactory.get(path)


def test_bad_override_path_raises_value_error():
    path = Path("tests/resources/invalid/targets-extends-bad-override.yaml").resolve()
    with pytest.raises(RegistryLoadError):
        RegistryFactory.get(path)
