"""Portable polling watch mode."""

from __future__ import annotations

import time
from pathlib import Path
from threading import Event
from typing import Callable


def snapshot(paths: list[str | Path]) -> dict[str, int]:
    files: dict[str, int] = {}
    for root in map(Path, paths):
        for path in root.rglob("*.py") if root.exists() else ():
            files[str(path.resolve())] = path.stat().st_mtime_ns
    return files


def watch(paths: list[str | Path], callback: Callable[[], None], *, interval: float = 0.5, stop: Event | None = None) -> None:
    if interval <= 0:
        raise ValueError("interval must be positive")
    stopper = stop or Event(); previous = snapshot(paths)
    while not stopper.wait(interval):
        current = snapshot(paths)
        if current != previous:
            previous = current
            callback()
