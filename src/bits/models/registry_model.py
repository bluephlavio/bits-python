from typing import Dict, List

from pydantic import BaseModel  # pylint: disable=no-name-in-module

from .bit_model import BitModel
from .constant_model import ConstantModel
from .target_model import TargetModel


class RegistryDataModel(BaseModel):
    tags: List[str] | None = None
    imports: List[Dict[str, str]] = []
    targets: List[TargetModel] = []
    constants: List[ConstantModel] = []
    bits: List[BitModel] = []
