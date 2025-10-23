from pathlib import Path
from bits.registry.registry_factory import RegistryFactory


def test_compose_dedupe_by_name_removes_duplicates():
    path = Path("tests/resources/compose-dedupe.yaml")
    registry = RegistryFactory.get(path)
    tex = registry.targets[0].render_tex_code()
    assert tex.count("$x+1=0$") == 1
