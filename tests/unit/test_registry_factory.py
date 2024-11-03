import unittest
from pathlib import Path

from bits.registry.registry_factory import RegistryFactory
from bits.registry.registryfile import RegistryFile
from bits.registry.registryfolder import RegistryFolder


class TestRegistryFactory(unittest.TestCase):
    def test_registry_factory_with_index_file(self):
        path_with_index = Path("tests/resources/folder-with-index")
        registry = RegistryFactory.get(path_with_index)
        self.assertIsInstance(registry, RegistryFile)

    def test_registry_factory_without_index_file(self):
        path_without_index = Path("tests/resources/folder-without-index")
        registry = RegistryFactory.get(path_without_index)
        self.assertIsInstance(registry, RegistryFolder)


if __name__ == "__main__":
    unittest.main()
