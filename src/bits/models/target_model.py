from pydantic import BaseModel  # pylint: disable=no-name-in-module


class TargetModel(BaseModel):  # pylint: disable=too-few-public-methods
    name: str | None = None
    tags: list[str] = []
    template: str | None = None
    context: dict = {}
    dest: str | None = None
