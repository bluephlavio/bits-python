from typing import Dict, List, Any

from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module


class BitModel(BaseModel):
    name: str | None = None
    num: int | None = None
    tags: List[str] = []
    defaults: Dict[str, Any] = {}
    src: str = Field(..., alias="src")
