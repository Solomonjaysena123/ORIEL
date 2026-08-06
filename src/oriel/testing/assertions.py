"""Small, dependency-free assertions including deterministic snapshots."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, TypeVar

E = TypeVar("E", bound=BaseException)


def assert_contains(member: object, container: object) -> None:
    if member not in container:  # type: ignore[operator]
        raise AssertionError(f"{member!r} not found in {container!r}")


@contextmanager
def assert_raises(error: type[E]) -> Iterator[None]:
    try:
        yield
    except error:
        return
    except BaseException as exc:
        raise AssertionError(f"expected {error.__name__}, got {type(exc).__name__}") from exc
    raise AssertionError(f"expected {error.__name__} to be raised")


def _serialize(value: object) -> str:
    if isinstance(value, str):
        return value.rstrip() + "\n"
    return json.dumps(value, indent=2, sort_keys=True, default=repr, ensure_ascii=False) + "\n"


def assert_snapshot(value: object, path: str | Path, *, update: bool | None = None) -> None:
    target = Path(path)
    actual = _serialize(value)
    should_update = update if update is not None else os.getenv("ORIEL_UPDATE_SNAPSHOTS") == "1"
    if should_update or not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(actual, encoding="utf-8")
        return
    expected = target.read_text(encoding="utf-8")
    if actual != expected:
        raise AssertionError(f"snapshot mismatch: {target}\nexpected: {expected!r}\nactual: {actual!r}")
