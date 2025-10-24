import itertools
import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def resources():
    path = Path(__file__).parent / "resources"
    return path.resolve()


@pytest.fixture(scope="session")
def bitsfiles(resources):  # pylint: disable=redefined-outer-name
    """Return all valid registry files for e2e CLI build.

    - Recurses under tests/resources
    - Skips anything under an 'invalid/' directory
    - Picks .md, .yaml, .yml files
    """
    patterns = ["*.md", "*.yaml", "*.yml"]
    files = []
    for pattern in patterns:
        for file in resources.rglob(pattern):
            # Exclude invalid fixture folders
            if "/invalid/" in str(file.as_posix()):
                continue
            files.append(file.resolve())
    # Deterministic order for stable CI
    files = sorted(set(files))
    return files


# Ensure tests run without a repo-level .bitsrc by pointing to tests/resources/.bitsrc
BITS_CONFIG_FILE = (Path(__file__).parent / "resources" / ".bitsrc").resolve()
os.environ.setdefault("BITS_CONFIG", str(BITS_CONFIG_FILE))
