# ORIEL 0.9.0

**Milestone:** Shared Application Framework Kernel

ORIEL 0.9.0 introduces the shared application foundation for later API, database, web, mobile, and security frameworks: lifecycle management, immutable environment configuration, service resolution, application events, health checks, and structured results. The complete v0.8.3 QA framework remains included.

## Install

```bash
python -m pip install dist/oriel_language-0.9.0-py3-none-any.whl
oriel version
```

## Test

```bash
python -m pip install pytest
python -m pytest
oriel-qa tests --workers 2 --retries 1 --fail-on-flaky
```

## VS Code

Install `dist/oriel-language-support-0.9.0.vsix` using **Extensions -> Install from VSIX**.

## Documentation

See [Shared Application Framework Kernel](docs/APPLICATION_KERNEL_0.9.0.md) and [QA Automation](docs/QA_AUTOMATION.md).
