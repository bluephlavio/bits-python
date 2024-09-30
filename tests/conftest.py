from pathlib import Path
import itertools

import pytest


@pytest.fixture(scope="session")
def resources():
    path = Path(__file__).parent / "resources"
    return path.resolve()


@pytest.fixture(scope="session")
def bitsfiles(resources):  # pylint: disable=redefined-outer-name
    patterns = ["*.md", "*.yaml", "*.yml"]
    return list(
        itertools.chain.from_iterable(
            (file.resolve() for file in resources.glob(pattern)) for pattern in patterns
        )
    )
