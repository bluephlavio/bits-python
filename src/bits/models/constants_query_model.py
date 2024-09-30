from typing import List

from pydantic import BaseModel  # pylint: disable=no-name-in-module


class ConstantsQueryModel(BaseModel):  # pylint: disable=too-few-public-methods
    id_: str | None = None
    name: str | None = None
    tags: List[str] = None
