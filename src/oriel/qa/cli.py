"""Command-line interface for ``oriel-qa``."""

from __future__ import annotations

import argparse
from pathlib import Path

from .reports import write_html, write_json, write_junit
from .runner import QARunner
from .watch import watch


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="oriel-qa", description="Run ORIEL QA automation")
    parser.add_argument("path", nargs="?", default="tests")
    parser.add_argument("--pattern", default="test*.py")
    parser.add_argument("--retries", type=int, default=0)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--report-dir", default="qa-reports")
    parser.add_argument("--category", action="append", help="Run only this category; repeat as needed")
    parser.add_argument("--fail-on-flaky", action="store_true", help="Return non-zero when retries hide a failure")
    parser.add_argument("--list", action="store_true", help="List discovered test IDs without running them")
    parser.add_argument("--watch", action="store_true")
    return parser


def execute(args: argparse.Namespace) -> int:
    runner = QARunner(retries=args.retries, workers=args.workers, categories=set(args.category or ()))
    tests = runner.discover(args.path, args.pattern)
    if args.list:
        for test in tests:
            print(test.id())
        return 0
    summary = runner.run(tests)
    report_dir = Path(args.report_dir)
    write_junit(summary, report_dir / "junit.xml")
    write_html(summary, report_dir / "report.html")
    write_json(summary, report_dir / "report.json")
    print(f"{summary.passed} passed, {summary.failed} failed, {summary.skipped} skipped, {summary.flaky} flaky")
    return 0 if summary.successful and not (args.fail_on_flaky and summary.flaky) else 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    code = execute(args)
    if args.watch:
        try:
            watch([args.path, "src"], lambda: execute(args))
        except KeyboardInterrupt:
            pass
    return code


if __name__ == "__main__":
    raise SystemExit(main())
