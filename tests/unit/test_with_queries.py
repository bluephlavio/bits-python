from pathlib import Path
from bits.registry.registry_factory import RegistryFactory


def test_with_queries_overlays_nested_blocks_for_composer():
    path = Path("tests/resources/with-queries-composer.yaml")
    registry = RegistryFactory.get(path)
    tex = registry.targets[0].render_tex_code()
    # Composer loops blocks; with.queries injects blocks list with single Eq => expect one equation
    assert tex.count("$x+1=0$") == 1
