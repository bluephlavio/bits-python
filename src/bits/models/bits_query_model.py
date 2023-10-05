from typing import List

from pydantic import BaseModel  # pylint: disable=no-name-in-module


class BitsQueryModel(BaseModel):  # pylint: disable=too-few-public-methods
    id_: str | None = None
    name: str | None = None
    tags: List[str] = None
    num: int | None = None
    author: str | None = None
    kind: str | None = None
    level: int | None = None
