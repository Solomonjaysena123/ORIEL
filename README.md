# ORIEL 0.9.1

**Milestone:** Database Application Framework

ORIEL 0.9.1 promotes the SQLite database layer into a migration and transaction framework with deterministic history, schema validation, explicit rollback behavior, parameterized queries, inspection, and health checks. The v0.9.0 Shared Application Kernel and complete v0.8.3 QA framework remain included.

## Install

```bash
python -m pip install dist/oriel_language-0.9.1-py3-none-any.whl
oriel version
```

## Test

```bash
python -m pip install pytest
python -m pytest
oriel-qa tests --workers 2 --retries 1 --fail-on-flaky
```

## VS Code

Install `dist/oriel-language-support-0.9.1.vsix` using **Extensions -> Install from VSIX**.

## Documentation

See [Database Framework](docs/DATABASE_FRAMEWORK_0.9.1.md), [Shared Application Framework Kernel](docs/APPLICATION_KERNEL_0.9.0.md), and [QA Automation](docs/QA_AUTOMATION.md).
