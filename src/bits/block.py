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
        self.metadata: dict = {**Block.process_metadata(metadata or {})}

    @staticmethod
    def process_metadata(metadata: dict):
        result = {**metadata}
        if "pts" in metadata and isinstance(metadata["pts"], list):
            result["total_pts"] = sum(metadata["pts"])
        return result

    def render(self):
        return self.bit.render(**self.context)
