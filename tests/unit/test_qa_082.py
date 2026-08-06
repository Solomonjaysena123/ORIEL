from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree

from oriel.qa import CheckRequest, QARunner, write_html, write_json, write_junit
from oriel.qa.api import APIAdapter
from oriel.qa.coverage import measure
from oriel.qa.watch import snapshot
from oriel.testing import Mock, assert_contains, assert_raises, assert_snapshot, fixture, parameterized, patch


class PrimitiveTests(unittest.TestCase):
    @parameterized(((1, 2, 3), (4, 5, 9)))
    def test_parameterized(self, left, right, expected):
        self.assertEqual(left + right, expected)

    def test_assertions_and_snapshot(self):
        assert_contains("ri", "oriel")
        with assert_raises(ValueError):
            raise ValueError("expected")
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "value.snap"
            assert_snapshot({"version": "0.8.2"}, target)
            assert_snapshot({"version": "0.8.2"}, target)
            with self.assertRaises(AssertionError):
                assert_snapshot({"version": "different"}, target)

    def test_fixture_cleanup_and_mock_exports(self):
        cleaned = []
        resource = fixture(lambda: {"ready": True}, lambda value: cleaned.append(value))
        with resource.use() as value:
            self.assertTrue(value["ready"])
        self.assertEqual(cleaned, [{"ready": True}])
        mocked = Mock(return_value=3)
        self.assertEqual(mocked(), 3)
        with patch("oriel.__version__", "test"):
            import oriel
            self.assertEqual(oriel.__version__, "test")


class _Pass(unittest.TestCase):
    def run_case(self):
        self.assertTrue(True)


class _Skip(unittest.TestCase):
    @unittest.skip("demonstration")
    def run_case(self):
        pass


class _Flaky(unittest.TestCase):
    calls = 0
    def run_case(self):
        type(self).calls += 1
        self.assertGreaterEqual(type(self).calls, 2)


class RunnerAndReportTests(unittest.TestCase):
    def setUp(self):
        _Flaky.calls = 0

    def test_retry_flaky_detection_and_reports(self):
        summary = QARunner(retries=1, workers=2).run([_Pass("run_case"), _Skip("run_case"), _Flaky("run_case")])
        self.assertTrue(summary.successful)
        self.assertEqual((summary.passed, summary.skipped, summary.flaky), (2, 1, 1))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            junit = write_junit(summary, root / "junit.xml")
            report = write_html(summary, root / "report.html")
            data = write_json(summary, root / "report.json")
            self.assertEqual(ElementTree.parse(junit).getroot().tag, "testsuite")
            self.assertIn("ORIEL QA Report", report.read_text(encoding="utf-8"))
            self.assertIn('"results"', data.read_text(encoding="utf-8"))

    def test_parallel_runs_are_result_isolated(self):
        summary = QARunner(workers=3).run([_Pass("run_case") for _ in range(8)])
        self.assertEqual(summary.passed, 8)
        self.assertEqual(len({id(result.attempts) for result in summary.results}), 8)

    def test_coverage_and_watch_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "sample.py"
            source.write_text("def value():\n    return 42\n", encoding="utf-8")
            namespace = {}
            code = compile(source.read_text(), str(source), "exec")
            exec(code, namespace)
            value, coverage = measure(namespace["value"], source_root=folder)
            self.assertEqual(value, 42)
            self.assertTrue(coverage)
            self.assertIn(str(source.resolve()), snapshot([folder]))

    def test_specialized_adapter_is_explicit_stub(self):
        with self.assertRaisesRegex(NotImplementedError, "api testing"):
            APIAdapter().check(CheckRequest("https://example.invalid"))
