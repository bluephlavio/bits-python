from pathlib import Path

from bits.registry.registry_factory import RegistryFactory


def test_queries_and_compose_flatten_concat():
    path = Path("tests/resources/queries-compose-yaml.yaml")
    registry = RegistryFactory.get(path)

    assert len(registry.targets) == 1
    target = registry.targets[0]

    tex = target.render_tex_code()

    # Should contain rendered content from the matching bit
    assert "Calculate the mass of the Sun" in tex
    # And the section header from template to ensure general render happened
    assert "\\section*{Quesiti}" in tex
