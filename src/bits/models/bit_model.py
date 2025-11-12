from typing import Any, Dict, List, Union

from pydantic import BaseModel, Field, validator  # pylint: disable=no-name-in-module


class BitModel(BaseModel):
    name: str | None = None
    num: int | None = None
    tags: List[str] = []
    author: str | None = None
    level: int | None = None
    kind: str | None = None
    defaults: Dict[str, Any] = {}
    presets: List[Dict[str, Any]] = []
    # src can be a single template string or a mapping of named fragments
    src: Union[str, Dict[str, str]] = Field(..., alias="src")

    @validator("src")
    def _validate_src(cls, v):  # noqa: N805 - pydantic signature
        # Allow simple string
        if isinstance(v, str):
            return v
        # Validate mapping form
        if isinstance(v, dict):
            if not v:
                raise ValueError("src mapping must not be empty")
            for k, val in v.items():
                if not isinstance(k, str):
                    raise ValueError("src mapping keys must be strings")
                if not isinstance(val, str):
                    raise ValueError("src mapping values must be strings")
            return v
        raise ValueError("src must be a string or a mapping of strings")
