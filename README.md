# ORIEL 0.8.3

**Milestone:** QA Automation Stabilization

ORIEL 0.8.3 stabilizes the dependency-free QA framework with category filtering, discovery listing, strict flaky-test quality gates, corrected JUnit semantics, aggregate coverage summaries, and stronger concurrency-safe regression tests.

## Install

```bash
python -m pip install dist/oriel_language-0.8.3-py3-none-any.whl
oriel version
```

## Test

```bash
python -m pip install pytest
python -m pytest
oriel-qa tests --workers 2 --retries 1 --fail-on-flaky
```

## VS Code

Install `dist/oriel-language-support-0.8.3.vsix` using **Extensions -> Install from VSIX**.

## Documentation

See [QA Automation](docs/QA_AUTOMATION.md) for authoring, execution, reports, coverage, extension adapters, and documented limitations.
