"""Parameterized subtests for unittest-style methods."""

from __future__ import annotations

from functools import wraps
from typing import Callable, Iterable, ParamSpec

P = ParamSpec("P")


def parameterized(cases: Iterable[tuple[object, ...]]) -> Callable[[Callable[..., None]], Callable[..., None]]:
    frozen = tuple(tuple(case) for case in cases)

    def decorate(function: Callable[..., None]) -> Callable[..., None]:
        @wraps(function)
        def wrapper(self: object) -> None:
            subtest = getattr(self, "subTest", None)
            for index, case in enumerate(frozen):
                if subtest:
                    with subtest(case=index, parameters=case):
                        function(self, *case)
                else:
                    function(self, *case)
        return wrapper
    return decorate
