import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bits.models import BitModel, ConstantModel, RegistryDataModel, TargetModel
from bits.registry.registryfile_dumpers import RegistryFileDumperFactory
from bits.registry.registryfile_parsers import RegistryFileParserFactory


class TestRegistryFileParsersDumpers(unittest.TestCase):
    def setUp(self):
        self.sample_data = RegistryDataModel(
            tags=["sample"],
            bits=[
                BitModel(name="Sample Bit", src="$x + 1 = 0$", tags=["math"]),
            ],
            constants=[
                ConstantModel(name="Sample Constant", symbol="SC", value=42),
            ],
            targets=[
                TargetModel(name="Sample Target", context={"key": "value"}),
            ],
            imports=[],
        )

    def test_yaml_parser_dumper(self):
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_registry.yml"
            dumper = RegistryFileDumperFactory.get(path)
            dumper.dump(self.sample_data, path)

            parser = RegistryFileParserFactory.get(path)
            parsed_data = parser.parse(path)

            self.assertEqual(self.sample_data.dict(), parsed_data.dict())

    def test_md_parser_dumper(self):
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_registry.md"
            dumper = RegistryFileDumperFactory.get(path)
            dumper.dump(self.sample_data, path)

            parser = RegistryFileParserFactory.get(path)
            parsed_data = parser.parse(path)

            self.assertEqual(self.sample_data.dict(), parsed_data.dict())


if __name__ == "__main__":
    unittest.main()
