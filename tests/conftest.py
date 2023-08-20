from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def resources():
    path = Path(__file__).parent / "resources"
    return path.resolve()


@pytest.fixture(scope="session")
def bitsfile(resources):  # pylint: disable=redefined-outer-name
    path = resources / "bitsfile.md"
    return path.resolve()
