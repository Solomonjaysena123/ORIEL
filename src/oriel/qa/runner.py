"""Discovery, retries and parallel execution for unittest-compatible suites."""

from __future__ import annotations

import io
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .models import Attempt, RunSummary, TestResult


def _flatten(suite: unittest.TestSuite) -> list[unittest.TestCase]:
    tests: list[unittest.TestCase] = []
    for item in suite:
        tests.extend(_flatten(item) if isinstance(item, unittest.TestSuite) else [item])
    return tests


def _category(test: unittest.TestCase) -> str:
    value = getattr(test, "qa_category", None) or getattr(test.__class__, "qa_category", None)
    if value:
        return str(value)
    name = test.id().lower()
    for candidate in ("integration", "regression", "snapshot"):
        if candidate in name:
            return candidate
    return "unit"


def _run_once(test: unittest.TestCase) -> Attempt:
    stream = io.StringIO()
    started = time.perf_counter()
    result = unittest.TextTestRunner(stream=stream, verbosity=0).run(test)
    status = "passed"
    if result.skipped:
        status = "skipped"
    elif result.failures:
        status = "failed"
    elif result.errors:
        status = "error"
    return Attempt(status, time.perf_counter() - started, stream.getvalue().strip())


def _run_test(test: unittest.TestCase, retries: int) -> TestResult:
    outcome = TestResult(test.id(), _category(test))
    for attempt_number in range(retries + 1):
        if attempt_number == 0:
            current = test
        else:
            try:
                current = test.__class__(test._testMethodName)
            except TypeError:
                # Loader failures and custom cases may require constructor state.
                # Preserve their first error instead of crashing the QA runner.
                break
        outcome.attempts.append(_run_once(current))
        if outcome.status in {"passed", "skipped"}:
            break
    return outcome


class QARunner:
    def __init__(self, *, retries: int = 0, workers: int = 1, categories: set[str] | None = None) -> None:
        if retries < 0 or workers < 1:
            raise ValueError("retries must be non-negative and workers must be positive")
        self.retries, self.workers = retries, workers
        self.categories = {value.lower() for value in categories} if categories else None

    def discover(self, start_dir: str | Path = "tests", pattern: str = "test*.py") -> list[unittest.TestCase]:
        return _flatten(unittest.defaultTestLoader.discover(str(start_dir), pattern=pattern))

    def run(self, tests: list[unittest.TestCase]) -> RunSummary:
        started = time.perf_counter()
        if self.categories is not None:
            tests = [test for test in tests if _category(test).lower() in self.categories]
        if self.workers == 1:
            results = [_run_test(test, self.retries) for test in tests]
        else:
            with ThreadPoolExecutor(max_workers=self.workers, thread_name_prefix="oriel-qa") as pool:
                results = list(pool.map(lambda test: _run_test(test, self.retries), tests))
        return RunSummary(results, time.perf_counter() - started)
