# ORIEL 0.9.4

**Milestone:** Web Framework

ORIEL 0.9.4 adds a dependency-free, transport-independent web framework with typed routing, middleware, lifecycle hooks, safe server-rendered templates, forms, JSON, signed sessions, CSRF protection, static assets, a development server, and an in-process test client.

The hardened v0.9.3 Authentication and Security Framework, v0.9.2 API Framework, v0.9.1 Database Framework, v0.9.0 Shared Application Kernel, and complete QA framework remain included.

## Install

```bash
python -m pip install dist/oriel_language-0.9.4-py3-none-any.whl
oriel version
```

## Create and run a web project

```bash
oriel web new my_site
cd my_site
oriel web serve src/app.py
```

The development server binds to `127.0.0.1:8080` by default. Use `--host` and `--port` to change it.

## Test

```bash
python -m pip install pytest
python -m pytest
oriel-qa tests --workers 2 --retries 1 --fail-on-flaky
```

## VS Code

Install `dist/oriel-language-support-0.9.4.vsix` using **Extensions -> Install from VSIX**.

## Documentation

See [Web Framework](docs/WEB_FRAMEWORK_0.9.4.md), [Authentication and Security](docs/SECURITY_FRAMEWORK_0.9.3.md), [API Framework](docs/API_FRAMEWORK_0.9.2.md), [Database Framework](docs/DATABASE_FRAMEWORK_0.9.1.md), [Shared Application Framework Kernel](docs/APPLICATION_KERNEL_0.9.0.md), and [QA Automation](docs/QA_AUTOMATION.md).

ORIEL is distributed under the [MIT License](LICENSE).
