from bits.bit import Bit
from bits.block import Block


def test_block_render_allows_per_call_overrides():
    bit = Bit(src={"left": r"\VAR{ x }"}, defaults={"x": 1}, name="Assoc")
    block = Block(bit, context={"x": 2})

    # Baseline: block context overrides bit defaults
    assert block.render("left") == "2"

    # Per-call kwargs override block context
    assert block.render("left", x=3) == "3"


def test_block_fragment_render_allows_per_call_overrides():
    bit = Bit(src={"right": r"\VAR{ label }"}, defaults={"label": "X"}, name="Assoc")
    block = Block(bit, context={"label": "Y"})
    frag = block.fragment("right")

    # Baseline: fragment uses block context
    assert frag.render() == "Y"

    # Per-call kwargs override fragment context
    assert frag.render(label="Z") == "Z"

