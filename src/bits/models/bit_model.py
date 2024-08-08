from typing import Dict, List, Any

from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module


class BitModel(BaseModel):
    name: str | None = None
    tags: List[str] | None = None
    defaults: Dict[str, Any] | None = None
    src: str = Field(..., alias="src")
