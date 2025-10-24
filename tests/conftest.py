import itertools
import os
from pathlib import Path

import pytest
from bits.config import config


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

# Normalize commonly used variable paths to absolute to avoid registry-relative resolution
try:
    if not config.has_section("variables"):
        config.add_section("variables")
    # Ensure absolute paths for templates and artifacts
    for key, rel in {
        "templates": "tests/resources/templates",
        "artifacts": "tests/artifacts",
    }.items():
        val = config.get("variables", key, fallback=None)
        if not val:
            config.set("variables", key, str((Path(rel)).resolve()))
        else:
            p = Path(val)
            if not p.is_absolute():
                config.set("variables", key, str((Path.cwd() / p).resolve()))
except Exception:
    # Be forgiving in case config is not accessible during collection phase
    pass
