import re
import uuid
from typing import List, Union


class Element:
    def __init__(
        self, name: str | None = None, tags: Union[List[str], None] = None, **kwargs
    ):
        self._metadata = {
            "id_": uuid.uuid4(),
            "name": name,
            "tags": tags or [],
            **kwargs,
        }

    def __repr__(self) -> str:
        cls_name: str = self.__class__.__name__
        kwargs_str: str = ", ".join(f"{k}={v}" for k, v in self._metadata.items())
        return f"{cls_name}({kwargs_str})"

    @property
    def id(self) -> str:  # pylint: disable=invalid-name
        return self._metadata["id_"]

    @property
    def name(self) -> str | None:
        return self._metadata["name"]

    @property
    def tags(self) -> List[str]:
        return self._metadata["tags"]

    def match_by_id(self, id_: str) -> bool:
        return self._metadata["id"] == id_

    def match_by_name(self, name: str | None) -> bool:
        if name is not None:
            pattern = re.compile(name)
            return bool(pattern.match(self._metadata["name"]))
        return True

    def match_by_tags(self, tags: List[str] | None) -> bool:
        if tags is not None and len(tags) > 0:
            return all(tag in self._metadata["tags"] for tag in tags)
        return True

    def match_by_metadata(self, key: str, value) -> bool:
        if value is not None:
            return self._metadata[key] == value
        return True
