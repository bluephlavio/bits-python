from pydantic import BaseModel  # pylint: disable=no-name-in-module

from .constants_query_model import ConstantsQueryModel


class ConstantsModel(BaseModel):  # pylint: disable=too-few-public-methods
    registry: str | None = None
    query: ConstantsQueryModel
    context: dict = {}
    metadata: dict = {}
