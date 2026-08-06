# ORIEL 0.9.7

**Milestone:** iOS/iPadOS and Unified Mobile Packaging

ORIEL 0.9.7 adds iOS/iPadOS packaging, UIKit rendering contracts, lifecycle and device APIs, privacy permissions, signing validation, Xcode build/archive commands, and unified Android+iOS projects. The complete v0.9.6 Android Framework remains included.

All earlier ORIEL language, QA, application-kernel, database, API, security, web, UI, Python compatibility, CI, and VS Code functionality remains included.

## Install

```bash
python -m pip install dist/oriel_language-0.9.6-py3-none-any.whl
oriel version
```

Python 3.10 through 3.12 are supported.

## Create an Android project

```bash
oriel android new DemoApp \
  --application-id org.example.demo \
  --version-name 1.0.0 \
  --version-code 1 \
  --permission notifications

oriel android validate DemoApp
oriel android build DemoApp
```

Building requires Java, Gradle, and an Android SDK configured through `ANDROID_SDK_ROOT` or `ANDROID_HOME`.

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

Install `dist/oriel-language-support-0.9.6.vsix` using **Extensions -> Install from VSIX**.

## Documentation

See [Android Framework](docs/ANDROID_FRAMEWORK_0.9.6.md), [Cross-Platform UI Engine](docs/CROSS_PLATFORM_UI_ENGINE_0.9.5.md), [Web Framework](docs/WEB_FRAMEWORK_0.9.4.md), [Authentication and Security](docs/SECURITY_FRAMEWORK_0.9.3.md), and [QA Automation](docs/QA_AUTOMATION.md).

ORIEL is distributed under the [MIT License](LICENSE).
