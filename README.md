# ORIEL 0.9.8

**Milestone:** Cross-Platform Desktop Framework

ORIEL 0.9.8 adds Windows, macOS, and Linux desktop project generation, windows, menus, tray icons, files, updates, deterministic packaging, native executable builds, and secure native interoperability. The complete v0.9.7 mobile framework remains included.

All earlier ORIEL language, QA, application-kernel, database, API, security, web, UI, Python compatibility, CI, and VS Code functionality remains included.

## Install

```bash
python -m pip install dist/oriel_language-0.9.8-py3-none-any.whl
oriel version
```

Python 3.10 through 3.12 are supported.

## Create a desktop project

```bash
oriel desktop new DemoDesk --application-id org.example.demo --version 1.0.0
oriel desktop validate DemoDesk
oriel desktop package DemoDesk --target windows
oriel desktop build DemoDesk
```

Native executable builds require PyInstaller and must run on the target operating system.

## Store-ready app bundle

Keep signing credentials outside the repository:

```bash
export ORIEL_ANDROID_KEYSTORE=/secure/release.jks
export ORIEL_ANDROID_STORE_PASSWORD=...
export ORIEL_ANDROID_KEY_ALIAS=release
export ORIEL_ANDROID_KEY_PASSWORD=...

oriel android validate DemoApp --store-ready
oriel android build DemoApp --bundle --release
```

## Test

```bash
python -m pip install pytest
python -m pytest
oriel-qa tests --workers 2 --retries 1 --fail-on-flaky
```

## VS Code

Install `dist/oriel-language-support-0.9.8.vsix` using **Extensions -> Install from VSIX**.

## Documentation

See [Desktop Framework](docs/DESKTOP_FRAMEWORK_0.9.8.md), [Mobile Framework](docs/MOBILE_FRAMEWORK_0.9.7.md), [Android Framework](docs/ANDROID_FRAMEWORK_0.9.6.md), [Cross-Platform UI Engine](docs/CROSS_PLATFORM_UI_ENGINE_0.9.5.md), and [QA Automation](docs/QA_AUTOMATION.md).

ORIEL is distributed under the [MIT License](LICENSE).
