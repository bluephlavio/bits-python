import pytest
from pathlib import Path

from bits.registry.registry_factory import RegistryFactory
from bits.exceptions import RegistryLoadError


def test_preset_bad_override_path_raises():
    path = Path("tests/resources/invalid/bits-presets-bad-override.yaml")
    with pytest.raises(RegistryLoadError):
        RegistryFactory.get(path)
