# ORIEL Android Framework 0.9.6

ORIEL 0.9.6 provides Android packaging and runtime abstractions for applications built on the v0.9.5 shared UI engine.

## Scope

This release includes:

- Gradle Kotlin Android application scaffolding;
- Android manifests, resources, package IDs, versions, SDK levels, and build types;
- an Android renderer contract for ORIEL UI trees;
- lifecycle, device information, safe URL launching, and vibration APIs;
- manifest-aware runtime permissions;
- local notification channels, immediate delivery, scheduling, and cancellation;
- constrained background work with retries and cancellation;
- debug APK and release APK/AAB commands;
- environment-only signing and store-readiness validation;
- deterministic mock backends for tests without an emulator.

Push-provider registration, Play Console submission, and native device execution require external services or Android tooling and credentials.

## Project generation

```bash
oriel android new DemoApp \
  --application-id org.example.demo \
  --version-name 1.0.0 \
  --version-code 1 \
  --min-sdk 24 \
  --target-sdk 35 \
  --compile-sdk 35 \
  --permission camera \
  --permission notifications
```

Generated projects contain Gradle Kotlin scripts, a secure Android manifest, resources, Kotlin launcher activity, ORIEL metadata, ProGuard configuration, and ignore rules for builds and signing keys.

Application IDs must use reverse-domain notation. SDK levels must satisfy `21 <= minSdk <= targetSdk <= compileSdk`.

## UI rendering

```python
from oriel.android_framework import AndroidRenderer
from oriel.ui_engine import UIContext, column, text

tree = column(text("ORIEL Android"), gap=16)
rendered = AndroidRenderer().render(tree, UIContext(platform="android"))
```

`AndroidRenderer` maps shared nodes to Android view contracts:

- flex containers to `LinearLayout`;
- grids to `GridLayout`;
- stacks to `FrameLayout`;
- text and headings to `TextView`;
- buttons, inputs, and images to their corresponding Android view types.

Layout, accessibility descriptions, enabled state, headings, keys, and diagnostics are retained for native adapters.

## Lifecycle and permissions

`AndroidLifecycle` enforces valid created, started, resumed, paused, stopped, and destroyed transitions.

`PermissionManager` refuses requests not declared in the generated manifest. Applications can query, request, and require typed `AndroidPermission` values. `MockAndroidDevice` provides deterministic permission responses in automated tests.

## Notifications

`NotificationManager` requires registered channels before publication. It supports immediate notifications, future delivery, deterministic due-item ordering, and cancellation. Platform integrations implement the small `NotificationBackend` protocol.

## Background work

`BackgroundWorkManager` supports:

- initial delay;
- connected or unmetered network requirements;
- charging, idle, and battery constraints;
- cancellation;
- JSON-serializable payloads;
- exponential retry backoff;
- bounded attempt counts.

The manager is a deterministic framework contract. A native adapter can translate requests into Android WorkManager jobs.

## Packaging and signing

```bash
oriel android validate DemoApp
oriel android build DemoApp
```

Release signing uses these environment variables:

- `ORIEL_ANDROID_KEYSTORE`
- `ORIEL_ANDROID_STORE_PASSWORD`
- `ORIEL_ANDROID_KEY_ALIAS`
- `ORIEL_ANDROID_KEY_PASSWORD`

Signing values are never written into generated source. Store validation rejects embedded `.jks` or `.keystore` files, debuggable manifests, missing signing configuration, cleartext traffic, malformed manifests, and incomplete Gradle metadata.

```bash
oriel android validate DemoApp --store-ready
oriel android build DemoApp --bundle --release
```

## Toolchain requirements and current verification boundary

Real APK/AAB builds require:

- Java and a JDK;
- Gradle;
- Android SDK tools and an installed compile SDK;
- `ANDROID_SDK_ROOT` or `ANDROID_HOME`.

Device tests additionally require ADB and an emulator or Android device. Play Store submission requires a developer account, signing credentials, listing assets, and policy declarations.

The repository's Android CI workflow generates a fresh project and builds a debug APK with Java 17, Gradle 8.9, and the hosted Android SDK. Signed release bundles remain credential-dependent.
