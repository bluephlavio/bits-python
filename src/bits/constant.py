from .collections import Element
from .models import ConstantModel


class Constant(Element):
    def __init__(self, name: str, symbol: str, value: str, tags=None):
        super().__init__(name=name, tags=tags)
        self.symbol = symbol
        self.value = value

    def __str__(self):
        return f"{self.symbol} = {self.value}"

    def __repr__(self):
        return f"Constant({self.name}, {self.symbol}, {self.value}, {self.tags})"

    @classmethod
    def from_model(cls, model: ConstantModel) -> "Constant":
        return cls(model.name, model.symbol, model.value, model.tags)

    def to_model(self) -> ConstantModel:
        return ConstantModel(
            name=self.name, symbol=self.symbol, value=self.value, tags=self.tags
        )
