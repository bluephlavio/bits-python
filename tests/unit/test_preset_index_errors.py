import pytest
from pathlib import Path

from bits.registry.registry_factory import RegistryFactory
from bits.exceptions import RegistryLoadError


def test_preset_index_out_of_range_raises():
    path = Path("tests/resources/invalid/preset-out-of-range.yaml")
    with pytest.raises(RegistryLoadError):
        RegistryFactory.get(path)
