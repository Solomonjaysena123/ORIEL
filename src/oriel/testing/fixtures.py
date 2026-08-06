"""Fixtures with explicit setup and guaranteed teardown."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Callable, Generic, Iterator, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Fixture(Generic[T]):
    factory: Callable[[], T]
    cleanup: Callable[[T], None] | None = None

    @contextmanager
    def use(self) -> Iterator[T]:
        value = self.factory()
        try:
            yield value
        finally:
            if self.cleanup:
                self.cleanup(value)


def fixture(factory: Callable[[], T], cleanup: Callable[[T], None] | None = None) -> Fixture[T]:
    return Fixture(factory, cleanup)
