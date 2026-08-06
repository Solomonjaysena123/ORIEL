# ORIEL 0.9.5

**Milestone:** Cross-Platform UI Engine

ORIEL 0.9.5 introduces a backend-neutral, declarative UI foundation with reusable components, responsive layout primitives, observable state, renderer contracts, themes, localization, accessibility semantics, validation, memory rendering, and a safe HTML reference renderer.

The v0.9.4 Web Framework, hardened v0.9.3 Authentication and Security Framework, v0.9.2 API Framework, v0.9.1 Database Framework, v0.9.0 Shared Application Kernel, QA framework, and VS Code extension remain included.

## Install

```bash
python -m pip install dist/oriel_language-0.9.5-py3-none-any.whl
oriel version
```

Python 3.10 through 3.12 are supported. Python 3.10 automatically installs the lightweight `tomli` compatibility dependency.

## Create a UI project

```bash
oriel ui new my_app
cd my_app
```

Version 0.9.5 establishes the portable component, state, layout, theme, localization, accessibility, and renderer contracts. Dedicated Android, iOS, Windows, macOS, and Linux native renderers are future milestones.

## Test

```bash
python -m pip install pytest
python -m pytest
oriel-qa tests --workers 2 --retries 1 --fail-on-flaky
```

## VS Code

Install `dist/oriel-language-support-0.9.5.vsix` using **Extensions -> Install from VSIX**.

## Documentation

See [Cross-Platform UI Engine](docs/CROSS_PLATFORM_UI_ENGINE_0.9.5.md), [Web Framework](docs/WEB_FRAMEWORK_0.9.4.md), [Authentication and Security](docs/SECURITY_FRAMEWORK_0.9.3.md), [API Framework](docs/API_FRAMEWORK_0.9.2.md), [Database Framework](docs/DATABASE_FRAMEWORK_0.9.1.md), [Shared Application Framework Kernel](docs/APPLICATION_KERNEL_0.9.0.md), and [QA Automation](docs/QA_AUTOMATION.md).

ORIEL is distributed under the [MIT License](LICENSE).
