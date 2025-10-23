from pathlib import Path

from bits.registry.registry_factory import RegistryFactory


def test_preset_numeric_string_fallback_to_index():
    path = Path("tests/resources/bits-presets-string-index.yaml")
    registry = RegistryFactory.get(path)
    target = registry.targets[0]
    tex = target.render_tex_code()
    assert "Formula: B" in tex
