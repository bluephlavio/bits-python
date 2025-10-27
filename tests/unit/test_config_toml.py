import importlib
from pathlib import Path

from bits.env import EnvironmentFactory
from bits.config import config, load_config_file


def test_load_toml_plugins_and_booleans(tmp_path):
    plugin = (Path("tests/resources/plugins/math_filters.py").resolve()).as_posix()
    toml = f'''
[variables]
templates = "tests/resources/templates"
artifacts = "tests/artifacts"

[jinja]
plugins = ["{plugin}"]

[output]
pdf = true
tex = false
'''
    cfg = tmp_path / ".bits.toml"
    cfg.write_text(toml)

    # Merge TOML file into active config
    load_config_file(cfg)

    # Ensure fresh env
    EnvironmentFactory._env_cache.clear()  # pylint: disable=protected-access
    EnvironmentFactory.enable_plugins(True)

    # Plugins should be parsed and loaded; filter 'double' must exist
    env = EnvironmentFactory.get()
    assert "double" in env.filters
    assert env.filters["double"](2) == 4

    # Booleans should be available via getboolean
    assert config.getboolean("output", "pdf") is True
    assert config.getboolean("output", "tex") is False

