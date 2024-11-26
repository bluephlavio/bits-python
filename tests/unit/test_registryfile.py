import unittest
from pathlib import Path
from bits.registry.registryfile import RegistryFile
from bits.block import Block


class TestRegistryFile(unittest.TestCase):
    def setUp(self):
        self.registry_path = Path("tests/resources/collection.yml")
        self.registry = RegistryFile(self.registry_path)

    def test_resolve_blocks_without_query(self):
        blocks_data = {
            "registry": "tests/resources/collection.yml",
            "context": {},
            "metadata": {},
        }
        blocks = self.registry._resolve_blocks(blocks_data)
        self.assertTrue(len(blocks) > 0)
        for block in blocks:
            self.assertIsInstance(block, Block)


if __name__ == "__main__":
    unittest.main()
