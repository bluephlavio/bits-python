from pathlib import Path

from bits.registry.registry_factory import RegistryFactory


def test_where_select_with_compose_and_with_overrides():
    path = Path("tests/resources/queries-where-select-compose.yaml")
    registry = RegistryFactory.get(path)

    assert len(registry.targets) == 1
    target = registry.targets[0]

    tex = target.render_tex_code()

    # Check Equazione bits 1 and 3 were included via indices
    assert "$x+1=0$" in tex
    assert "$x^3+1=0$" in tex
    # Ensure Mass of the Sun is present
    assert "Calculate the mass of the Sun" in tex

    # Check section header to confirm overall render
    assert "\\section*{Quesiti}" in tex
