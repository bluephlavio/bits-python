from pydantic import BaseModel  # pylint: disable=no-name-in-module

from .bits_query_model import BitsQueryModel


class BlocksModel(BaseModel):  # pylint: disable=too-few-public-methods
    registry: str | None = None
    query: BitsQueryModel
    context: dict = {}
    metadata: dict = {}
