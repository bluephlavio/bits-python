from pathlib import Path

from bits.registry.registry_factory import RegistryFactory


def test_bits_presets_selection_by_id_and_index():
    path = Path("tests/resources/bits-presets.yaml")
    registry = RegistryFactory.get(path)

    assert len(registry.targets) == 1
    target = registry.targets[0]
    tex = target.render_tex_code()

    assert "Calculate the mass of the Sun" in tex
    # default preset text
    assert "M=\\frac{Fr^2}{Gm}" in tex
    # alt preset text should also appear
    assert "(alt)" in tex
