from pydantic import BaseModel  # pylint: disable=no-name-in-module


class TargetModel(BaseModel):  # pylint: disable=too-few-public-methods
    name: str | None = None
    tags: list[str] = []
    template: str | None = None
    dest: str | None = None
    # Static variables only (no blocks/constants at top level in new schema)
    context: dict = {}
    # Dynamic queries (e.g., blocks/constants); new schema field
    queries: dict = {}
    # Compose options for named queries or aggregations
    compose: dict = {}
