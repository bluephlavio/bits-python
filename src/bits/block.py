# pylint: disable=too-few-public-methods
from .bit import Bit


class _BlockFragment:
    def __init__(self, bit: Bit, name: str, context: dict):
        self._bit = bit
        self._name = name
        self._context = context

    def render(self, **extra) -> str:
        ctx = {**self._context, **extra}
        return self._bit.render(part=self._name, **ctx)


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

    def render(self, part: str | None = None, **extra) -> str:
        ctx = {**self.context, **extra}
        return self.bit.render(part=part, **ctx)

    def fragment(self, name: str) -> _BlockFragment:
        return _BlockFragment(self.bit, name, self.context)

    @property
    def fragments(self) -> dict:
        try:
            # Expose mapping: name -> fragment renderer bound to this block's context
            names = getattr(self.bit, "fragment_names", [])
            return {n: self.fragment(n) for n in names}
        except Exception:
            return {}
