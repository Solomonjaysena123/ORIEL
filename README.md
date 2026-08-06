# ORIEL 0.9.2

**Milestone:** API Application Framework

ORIEL 0.9.2 adds a transport-independent API dispatcher, path and query parameters, structured responses and errors, an in-process test client, OpenAPI 3.1 generation, and a threaded development server. The v0.9.1 Database Framework, v0.9.0 Shared Application Kernel, and complete QA framework remain included.

## Install

```bash
python -m pip install dist/oriel_language-0.9.2-py3-none-any.whl
oriel version
```

## Test

```bash
python -m pip install pytest
python -m pytest
oriel-qa tests --workers 2 --retries 1 --fail-on-flaky
```

## VS Code

Install `dist/oriel-language-support-0.9.2.vsix` using **Extensions -> Install from VSIX**.

## Documentation

See [API Framework](docs/API_FRAMEWORK_0.9.2.md), [Database Framework](docs/DATABASE_FRAMEWORK_0.9.1.md), [Shared Application Framework Kernel](docs/APPLICATION_KERNEL_0.9.0.md), and [QA Automation](docs/QA_AUTOMATION.md).
