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


class WhereBitsModel(BitsQueryModel):  # pylint: disable=too-few-public-methods
    # Additional predicates
    has: List[str] | None = None
    missing: List[str] | None = None


class SelectModel(BaseModel):  # pylint: disable=too-few-public-methods
    indices: List[int] | None = None  # 1-based
    k: int | None = None
    limit: int | None = None
    offset: int | None = None
    shuffle: bool | None = None
    seed: int | None = None
    sample: int | None = None
