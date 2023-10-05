from .bit import Bit


class Block:
    def __init__(
        self,
        bit: Bit,
        context: dict | None = None,
        metadata: dict | None = None,
    ):
        self.bit: Bit = bit
        self.context: dict = context or {}
        self.metadata: dict = metadata or {}

    def render(self):
        return self.bit.render(**self.context)
