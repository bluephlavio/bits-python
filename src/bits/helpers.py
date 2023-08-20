import hashlib
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

import yaml


def read(path: Path) -> str:
    with path.open() as f:  # pylint: disable=invalid-name
        return f.read()


def write(content: str, path: Path) -> None:
    with path.open("w") as f:  # pylint: disable=invalid-name
        f.write(content)


def load(path: Path) -> dict:
    with path.open() as f:  # pylint: disable=invalid-name
        return yaml.load(f, Loader=yaml.Loader)


def dump(data: dict, path: Path) -> None:
    content = yaml.dump(data, Dumper=yaml.Dumper, sort_keys=False)
    write(content, path)


def normalize_path(path: Path | str, relative_to: Path | str | None = None) -> Path:
    if relative_to:
        relative_to_dir: Path = normalize_path(
            Path(relative_to).parent if relative_to.suffix else relative_to
        )
        return normalize_path(relative_to_dir / path)
    return Path(path).expanduser().resolve()


def create_id_from_string(string: str) -> str:
    return hashlib.md5(bytes(string, "utf-8")).hexdigest()


@contextmanager
def tmpdir():
    cwd = os.getcwd()
    tmp_dir = tempfile.mkdtemp()
    os.chdir(tmp_dir)
    try:
        yield tmp_dir
    finally:
        os.chdir(cwd)
        shutil.rmtree(tmp_dir)
