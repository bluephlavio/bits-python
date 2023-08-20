from __future__ import annotations

from typing import Generic, List, MutableSequence, TypeVar

from .element import Element

T = TypeVar("T", bound=Element)


class Collection(Generic[T], MutableSequence[T]):
    def __init__(self, expected_type: type, collection: List[T] | None = None):
        self._expected_type = expected_type
        self._data = []
        if collection:
            for element in collection:
                self.append(element)

    def _check_type(self, value: T) -> None:
        if not isinstance(value, self._expected_type):
            raise TypeError(
                f"Expected type {self._expected_type}, but got {type(value)}"
            )

    def _check_if_already_exists(self, value: T) -> None:
        if value.id in map(lambda e: e.id, self._data):
            raise ValueError(f"Element with id {value.id} already exists")

    def _validate(self, value: T) -> None:
        self._check_type(value)
        self._check_if_already_exists(value)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}({self._expected_type.__name__},"
            f" [{', '.join(map(lambda e: e.__repr__(), self._data))}])"
        )

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, index: int) -> T:
        return self._data[index]

    def __setitem__(self, index: int, value: T) -> None:
        self._validate(value)
        self._data[index] = value

    def __delitem__(self, index: int) -> None:
        del self._data[index]

    def insert(self, index: int, value: T) -> None:
        self._validate(value)
        self._data.insert(index, value)

    def find_by_id(self, id_: str) -> T | None:
        element: T
        for element in self._data:
            if element.match_by_id(id_):
                return element
        raise ValueError(f"Element with id {id_} not found")

    def filter(
        self, name: str | None = None, tags: List[str] | None = None, **kwargs
    ) -> Collection[T]:
        result: Collection[T] = Collection(self._expected_type)
        element: T
        for element in self._data:
            if (
                element.match_by_name(name)
                and element.match_by_tags(tags)
                and all(element.match_by_metadata(k, v) for k, v in kwargs.items())
            ):
                result.append(element)
        return result

    def query(
        self,
        id_: str | None = None,
        name: str | None = None,
        tags: List[str] | None = None,
        **kwargs,
    ) -> Collection[T]:
        if id_:
            element: Element = self.find_by_id(id_)
            return Collection(self._expected_type, [element]).filter(
                name=name, tags=tags, **kwargs
            )
        return self.filter(name=name, tags=tags, **kwargs)
