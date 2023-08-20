from uuid import UUID

from bits.bit import Bit


def test_bit_id():
    bit: Bit = Bit(src="Hello World")
    assert isinstance(bit.id, UUID)
    assert isinstance(bit.id.hex, str)
