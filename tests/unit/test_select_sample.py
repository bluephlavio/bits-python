from pathlib import Path
from bits.registry.registry_factory import RegistryFactory


def test_select_sample_with_seed_picks_n_items():
    path = Path("tests/resources/select-sample.yaml")
    registry = RegistryFactory.get(path)
    tex = registry.targets[0].render_tex_code()
    # Should render exactly 2 questions
    assert tex.count("\\item") == 2
