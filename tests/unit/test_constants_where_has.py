from pathlib import Path
from bits.registry.registry_factory import RegistryFactory
from bits.models.constants_model import ConstantsModel
from bits.models.constants_query_model import WhereConstantsModel


def test_constants_where_has_filters_mixed_registry():
    path = Path("tests/resources/constants-has.yaml")
    registry = RegistryFactory.get(path)
    # Resolve constants via where.has only
    consts = registry._resolve_constants(  # pylint: disable=protected-access
        ConstantsModel(where=WhereConstantsModel(has=["name", "symbol", "value"]))
    )
    assert len(consts) >= 1
    # Check symbol present
    assert getattr(consts[0], "symbol", None) == "$G$"
