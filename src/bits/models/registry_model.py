
from typing import List

from pydantic import BaseModel # pylint: disable=no-name-in-module

from .bit_model import BitModel
from .constant_model import ConstantModel
from .target_model import TargetModel


class RegistryDataModel(BaseModel):
    bits: List[BitModel] = []
    constants: List[ConstantModel] = []
    targets: List[TargetModel] = []
