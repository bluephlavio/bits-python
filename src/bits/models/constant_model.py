from typing import List

from pydantic import BaseModel  # pylint: disable=no-name-in-module


class ConstantModel(BaseModel):
    name: str
    tags: List[str] | None = []
    symbol: str
    value: str
