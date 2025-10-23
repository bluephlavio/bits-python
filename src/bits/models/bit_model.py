from typing import Any, Dict, List

from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module


class BitModel(BaseModel):
    name: str | None = None
    num: int | None = None
    tags: List[str] = []
    author: str | None = None
    level: int | None = None
    kind: str | None = None
    defaults: Dict[str, Any] = {}
    presets: List[Dict[str, Any]] = []
    src: str = Field(..., alias="src")
