from typing import List

from ..yaml_loader import load_yaml
from ..bit import Bit
from ..models import TargetModel, BitModel
from ..target import Target
from .registryfile import RegistryFile


class RegistryYamlFile(RegistryFile):
    def _check_file_type(self):
        if not self._path.suffix in [".yaml", ".yml"]:
            raise ValueError("Expected a .yaml or .yml file")

    def load(self, as_dep: bool = False) -> None:
        with open(self._path, "r", encoding="utf-8") as file:
            registry_data = load_yaml(file.read())

        self._bits.clear()

        bits_data: List[dict] = registry_data.get("bits", [])

        for bit_data in bits_data:
            try:
                bit: Bit = self._parse_bit(bit_data)
                self._bits.append(bit)
            except AttributeError:
                continue

        for bit in self._bits:
            bit.defaults = self._parse_context(bit.defaults)

        if not as_dep:
            self._targets.clear()

            targets_data: List[TargetModel] = map(
                lambda data: TargetModel(**data), registry_data.get("targets", [])
            )

            for target_data in targets_data:
                target: Target = self._parse_target(target_data)
                self._targets.append(target)

    def _parse_bit(self, data: dict) -> Bit:
        bit_model: BitModel = BitModel(**data)

        content: str = bit_model.src.strip()
        meta: dict = bit_model.dict(exclude={"src"})

        bit: Bit = Bit(content, **meta)
        return bit
