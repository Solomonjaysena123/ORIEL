"""ORIEL QA automation framework."""

from .adapters import CheckRequest, CheckResult, QAAdapter, UnsupportedAdapter
from .models import Attempt, RunSummary, TestResult
from .reports import write_html, write_json, write_junit
from .runner import QARunner

__all__ = ["Attempt", "CheckRequest", "CheckResult", "QAAdapter", "QARunner", "RunSummary", "TestResult", "UnsupportedAdapter", "write_html", "write_json", "write_junit"]
