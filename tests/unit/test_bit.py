from uuid import UUID

import pytest
from pydantic import ValidationError

from bits.bit import Bit
from bits.models import BitModel


def test_bit_id():
    bit: Bit = Bit(src="Hello World")
    assert isinstance(bit.id, UUID)
    assert isinstance(bit.id.hex, str)


def test_bit_time_metadata_round_trip():
    bit = Bit(src="Hello World", time=15)

    assert bit.time == 15
    assert bit.to_model().time == 15


@pytest.mark.parametrize("time", [0, -1, 1.5, "15", True])
def test_bit_model_rejects_invalid_time(time):
    with pytest.raises(ValidationError):
        BitModel(src="Hello World", time=time)
