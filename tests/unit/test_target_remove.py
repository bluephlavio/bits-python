from pathlib import Path

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


def test_remove_list_item_in_overrides():
    path = Path("tests/resources/targets-remove.yaml").resolve()
    tex = render_tex(path, "Derived Remove Second")
    # Expect Q1 and Q3 present, Q2 removed
    i1 = tex.find("Q1")
    i3 = tex.find("Q3")
    assert i1 != -1 and i3 != -1
    assert tex.find("Q2") == -1
    assert i1 < i3


def test_remove_out_of_range_is_noop():
    path = Path("tests/resources/targets-remove.yaml").resolve()
    tex = render_tex(path, "Derived Remove OOR")
    # Out-of-range remove should be no-op (same as Base)
    assert tex.find("Q1") != -1
    assert tex.find("Q2") != -1
    assert tex.find("Q3") != -1
    assert tex.find("Q1") < tex.find("Q2") < tex.find("Q3")

