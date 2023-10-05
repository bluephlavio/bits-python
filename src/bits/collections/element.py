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

    def match_by_name(self, name: str) -> bool:
        if self.name is not None:
            pattern = re.compile(name)
            match = pattern.match(self.name)
            return bool(match)
        return False

    def match_by_tags(self, tags: List[str]) -> bool:
        if len(tags) > 0:
            return all(tag in self._metadata["tags"] for tag in tags)
        return False

    def match_by(self, key: str, value) -> bool:
        if value is not None:
            if key == "id":
                return self.match_by_id(value)
            if key == "name":
                return self.match_by_name(value)
            if key == "tags":
                return self.match_by_tags(value)
            try:
                return self._metadata[key] == value
            except KeyError:
                return False
        return False

    def match_query(self, **kwargs) -> bool:
        matches = [self.match_by(k, v) for k, v in kwargs.items() if v is not None]
        if len(matches) > 0:
            return all(matches)
        return False
