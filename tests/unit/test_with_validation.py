import pytest
from pathlib import Path

from bits.registry.registry_factory import RegistryFactory
from bits.exceptions import RegistryLoadError


def test_invalid_with_schema_raises_error():
    path = Path("tests/resources/invalid/invalid-with.yaml")
    with pytest.raises(RegistryLoadError):
        RegistryFactory.get(path)
