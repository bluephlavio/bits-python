from pydantic import BaseModel  # pylint: disable=no-name-in-module

from .bits_query_model import SelectModel
from .constants_query_model import ConstantsQueryModel, WhereConstantsModel


class ConstantsModel(BaseModel):  # pylint: disable=too-few-public-methods
    registry: str | None = None
    # Legacy
    query: ConstantsQueryModel | None = None
    # New DSL
    where: WhereConstantsModel | None = None
    select: SelectModel | None = None
    context: dict = {}
    metadata: dict = {}
