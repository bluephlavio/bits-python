# pylint: disable=protected-access
from pathlib import Path

from bits.models import BlocksModel, WhereBitsModel
from bits.registry.registry_factory import RegistryFactory


def test_filter_bits_by_time():
    registry = RegistryFactory.get(Path("tests/resources/bits-time.yaml"))

    blocks = registry._resolve_blocks(BlocksModel(where=WhereBitsModel(time=20)))

    assert [block.bit.name for block in blocks] == ["Medium exercise"]


def test_filter_bits_with_time_metadata():
    registry = RegistryFactory.get(Path("tests/resources/bits-time.yaml"))

    with_time = registry._resolve_blocks(
        BlocksModel(where=WhereBitsModel(has=["time"]))
    )
    without_time = registry._resolve_blocks(
        BlocksModel(where=WhereBitsModel(missing=["time"]))
    )

    assert [block.bit.name for block in with_time] == [
        "Short exercise",
        "Medium exercise",
    ]
    assert [block.bit.name for block in without_time] == ["Unestimated exercise"]
