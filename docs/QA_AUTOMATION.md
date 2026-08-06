# ORIEL QA Automation Framework (v0.8.3)

ORIEL QA is a dependency-free automation layer built on Python's stable `unittest` protocol. It supports unit, integration, regression, and snapshot suites; fixtures and mocks; parameterized cases; retries and flaky classification; parallel workers; coverage collection; watch mode; and machine-readable reports.

## Run tests

```console
oriel-qa tests --workers 4 --retries 1 --report-dir qa-reports
```

Use `--category integration` to select a suite category, repeat `--category` to select several categories, use `--list` to inspect discovery without execution, and use `--fail-on-flaky` in CI to reject tests that pass only after retry.

The command writes `junit.xml`, `report.html`, and `report.json` and exits non-zero when a test ultimately fails. Parallel mode uses threads and is intended for independent I/O-heavy tests. Tests that mutate process-global state should use one worker.

Set a suite category with `qa_category = "integration"` on a `unittest.TestCase`. Without an explicit category, paths or test IDs containing `integration`, `regression`, or `snapshot` are classified automatically; everything else is a unit test.

## Authoring primitives

```python
from oriel.testing import assert_snapshot, fixture, parameterized

database = fixture(connect, lambda connection: connection.close())

class ArithmeticTests(unittest.TestCase):
    @parameterized(((1, 2, 3), (2, 2, 4)))
    def test_add(self, left, right, expected):
        self.assertEqual(left + right, expected)
```

Snapshots are created when absent. Update existing snapshots only by passing `update=True` or setting `ORIEL_UPDATE_SNAPSHOTS=1`; review updated files before committing.

## Coverage and specialized adapters

`oriel.qa.coverage.measure` collects line execution using the standard library. It is intentionally lightweight: branch coverage and subprocess aggregation are future work.

The `api`, `database`, `web`, `mobile`, `performance`, `security`, and `ai` modules define provider adapter boundaries. Their default adapters raise `NotImplementedError`; users must install or implement a concrete driver. This keeps the core safe and dependency-free while providing stable interfaces for later packages.

## Current limitations

- Parallel workers share a process; CPU-bound isolation and crash containment require a future process executor.
- Watch mode polls Python file timestamps and does not debounce rapid edits.
- Coverage is line-only and covers code executed inside the measured callback.
- The specialized domains are interfaces, not bundled HTTP clients, browsers, devices, load generators, scanners, or model providers.
