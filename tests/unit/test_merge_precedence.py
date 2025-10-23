from pathlib import Path
from bits.registry.registry_factory import RegistryFactory
from bits.models.blocks_model import BlocksModel
from bits.models.bits_query_model import WhereBitsModel


def test_defaults_preset_with_precedence_merge():
    path = Path("tests/resources/merge-precedence.yaml")
    registry = RegistryFactory.get(path)
    data = BlocksModel.parse_obj({
        'where': {'name': 'Merge'},
        'preset': 'default',
        'with': {'context': {'nested': {'x': 9}}}
    })
    blocks = registry._resolve_blocks(data)  # pylint: disable=protected-access
    assert len(blocks) == 1
    ctx = blocks[0].context
    assert ctx["nested"]["x"] == 9
    assert ctx["nested"]["y"] == 2
    assert ctx["nested"]["z"] == 3
