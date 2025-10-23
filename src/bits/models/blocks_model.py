from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module

from .bits_query_model import BitsQueryModel, SelectModel, WhereBitsModel


class WithModel(BaseModel):  # pylint: disable=too-few-public-methods
    context: dict = {}
    queries: dict = {}

    class Config:
        extra = "forbid"


class BlocksModel(BaseModel):  # pylint: disable=too-few-public-methods
    registry: str | None = None
    # Legacy query field
    query: BitsQueryModel | None = None
    # New DSL
    where: WhereBitsModel | None = None
    select: SelectModel | None = None
    preset: str | int | None = None
    with_: WithModel | None = Field(default=None, alias="with")
    # Back-compat/context for nested structures
    context: dict = {}
    metadata: dict = {}
