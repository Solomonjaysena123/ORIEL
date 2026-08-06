"""JUnit XML, HTML and JSON report writers."""

from __future__ import annotations

import html
import json
from dataclasses import asdict
from pathlib import Path
from xml.etree import ElementTree as ET

from .models import RunSummary


def write_junit(summary: RunSummary, path: str | Path) -> Path:
    root = ET.Element("testsuite", tests=str(len(summary.results)), failures=str(summary.failed), skipped=str(summary.skipped), time=f"{summary.duration:.6f}")
    for result in summary.results:
        case = ET.SubElement(root, "testcase", name=result.test_id, classname=result.category, time=f"{result.duration:.6f}")
        if result.status == "skipped":
            ET.SubElement(case, "skipped")
        elif result.status != "passed":
            ET.SubElement(case, "failure", message=result.attempts[-1].message).text = result.attempts[-1].message
        if result.flaky:
            ET.SubElement(case, "system-out").text = "passed after retry; classified as flaky"
    target = Path(path); target.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(target, encoding="utf-8", xml_declaration=True)
    return target


def write_html(summary: RunSummary, path: str | Path) -> Path:
    rows = "".join(f"<tr><td>{html.escape(r.test_id)}</td><td>{r.category}</td><td>{r.status}</td><td>{r.duration:.3f}</td><td>{'yes' if r.flaky else 'no'}</td></tr>" for r in summary.results)
    body = f"""<!doctype html><html><head><meta charset='utf-8'><title>ORIEL QA Report</title><style>body{{font:14px system-ui;margin:2rem}}table{{border-collapse:collapse;width:100%}}th,td{{padding:.5rem;border:1px solid #ccc;text-align:left}}</style></head><body><h1>ORIEL QA Report</h1><p>Passed: {summary.passed} · Failed: {summary.failed} · Skipped: {summary.skipped} · Flaky: {summary.flaky}</p><table><thead><tr><th>Test</th><th>Category</th><th>Status</th><th>Seconds</th><th>Flaky</th></tr></thead><tbody>{rows}</tbody></table></body></html>"""
    target = Path(path); target.parent.mkdir(parents=True, exist_ok=True); target.write_text(body, encoding="utf-8")
    return target


def write_json(summary: RunSummary, path: str | Path) -> Path:
    target = Path(path); target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")
    return target
