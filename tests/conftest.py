from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def resources():
    path = Path(__file__).parent / "resources"
    return path.resolve()


@pytest.fixture(scope="session")
def bitsfiles(resources):  # pylint: disable=redefined-outer-name
    return [path.resolve() for path in resources.glob("*.md")]
