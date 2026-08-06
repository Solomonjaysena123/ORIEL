"""Standard-library line coverage collection."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, TypeVar

T = TypeVar("T")


def measure(function: Callable[..., T], *args: object, source_root: str | Path = "src", **kwargs: object) -> tuple[T, dict[str, float]]:
    root = Path(source_root).resolve()
    hit: dict[Path, set[int]] = {}
    def tracer(frame: object, event: str, arg: object):
        if event == "line":
            path = Path(frame.f_code.co_filename).resolve()  # type: ignore[attr-defined]
            if root == path or root in path.parents:
                hit.setdefault(path, set()).add(frame.f_lineno)  # type: ignore[attr-defined]
        return tracer
    previous = sys.gettrace()
    try:
        sys.settrace(tracer)
        result = function(*args, **kwargs)
    finally:
        sys.settrace(previous)
    coverage: dict[str, float] = {}
    for path, lines_hit in hit.items():
        source = path.read_text(encoding="utf-8").splitlines()
        executable = {number for number, line in enumerate(source, 1) if line.strip() and not line.lstrip().startswith("#")}
        coverage[str(path)] = round(100 * len(lines_hit & executable) / len(executable), 2) if executable else 100.0
    return result, coverage
