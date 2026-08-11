# Changelog

## 0.9.8 - Cross-Platform Desktop Framework

- Added Windows, macOS, and Linux desktop project generation, validation, and native executable builds.
- Added window, menu, shortcut, tray, file-dialog, clipboard, notification, safe-link, update, and native interoperability contracts.
- Added shared UI rendering, deterministic staging packages, SHA-256 checksums, signing-material checks, CLI commands, documentation, and multi-platform CI.

## 0.9.7 - iOS and Unified Mobile Packaging

- Added iOS/iPadOS configuration, UIKit rendering contracts, lifecycle/device APIs, permissions, signing validation, XcodeGen projects, and Xcode build/archive commands.
- Added unified Android+iOS project generation and cumulative validation.
- Added Info.plist privacy descriptions, background modes, device-family targeting, secret-material detection, deterministic mocks, and macOS simulator-build CI.

## 0.9.6 - Android Framework

- Added validated Android application configuration, Gradle Kotlin project generation, manifests, resources, Kotlin launcher source, and debug/release build profiles.
- Added an Android renderer for v0.9.5 component trees with linear, grid, and stack containers, layout metadata, diagnostics, and accessibility mapping.
- Added lifecycle state enforcement, typed device information and APIs, manifest-aware runtime permissions, and deterministic mock devices.
- Added notification channels, immediate and scheduled notifications, cancellation, and a memory notification backend.
- Added constrained background work with scheduling, cancellation, exponential retry backoff, attempt limits, and deterministic runtime conditions.
- Added store-readiness validation, environment-only signing configuration, embedded-key detection, toolchain detection, APK/AAB build commands, and Android CLI workflows.
- Preserved the complete v0.9.5 platform, Python 3.10 support, MIT licensing, CI matrix, release packaging, and VS Code distribution.

## 0.9.5 - Cross-Platform UI Engine

- Added immutable declarative nodes, reusable components, row/column/grid/stack layouts, constraints, spacing, alignment, wrapping, and flex growth.
- Added thread-safe observable state, reactive renderer bindings, backend-neutral renderer contracts, and deterministic memory rendering.
- Added inherited design-token themes, regional localization fallback, interpolation, pluralization, JSON bundles, and Unicode regression coverage.
- Added accessibility semantics, semantic heading output, image alternatives, duplicate-key diagnostics, and layout validation.
- Added a safe HTML reference renderer with escaping, URL-scheme restrictions, constrained CSS sizes and colors, ETags-independent output, and stack rendering.
- Added the `oriel ui new` workflow while preserving v0.9.4 web/security hardening, Python 3.10 support, CI, packaging, and the VS Code extension.

## 0.9.4 - Web Framework

- Added transport-independent web requests, responses, deterministic routing, typed parameters, named routes, route groups, and reverse URL generation.
- Added ordered middleware, routed lifecycle hooks, configurable error pages, safe templates, validated forms, JSON bodies, redirects, and static-file delivery.
- Added signed cookie sessions, CSRF protection, hardened response headers, cookie security defaults, header-injection defenses, and bounded session-token decoding.
- Added ETags, caching, an in-process test client, a threaded development server, and the `oriel web new` and `oriel web serve` workflows.
- Preserved and regression-tested the v0.9.3 authentication/security hardening and the v0.9.1 SQLite connection fixes.
- Corrected the legacy CI test command and declared the `tomli` compatibility dependency required on Python 3.10.

## 0.9.3 - Authentication and Security Framework

- Added salted PBKDF2-SHA256 password hashing with bounded work factors and rehash detection.
- Added versioned, scoped, expiring HMAC tokens with defensive payload validation.
- Added identities, permissions, expiring sessions, revocation, and session-bound CSRF tokens.
- Added thread-safe sliding-window rate limiting and framework-neutral security headers.
- Retained the API, Database, Kernel, QA frameworks, regression suite, and SQLite fixes.

## 0.9.2 - API Application Framework

- Added a transport-independent API dispatcher and in-process test client.
- Added path parameters, query values, JSON request bodies, and structured errors.
- Added method-not-allowed responses with `Allow` headers.
- Added OpenAPI 3.1 path-parameter metadata and consistent 0.9.2 defaults.
- Added a threaded development server sharing the same dispatcher.
- Retained the v0.9.1 Database Framework, v0.9.0 Shared Application Kernel, QA framework, and SQLite fixes.

## 0.9.1 - Database Application Framework

- Added deterministic, checksum-based and idempotent schema migrations.
- Added auditable migration history with compatibility for legacy migration tables.
- Added explicit commit/rollback transaction sessions and parameterized queries.
- Added duplicate entity and field validation, inspection, and health checks.
- Added the `oriel db status` command.
- Retained the v0.9.0 Shared Application Kernel, v0.8.3 QA framework, and SQLite lifecycle fixes.

## 0.9.0 - Shared Application Framework Kernel

- Added deterministic application lifecycle management and reverse-order shutdown.
- Added immutable environment configuration and required-value validation.
- Added singleton/transient services with circular-dependency detection.
- Added thread-safe synchronous events and unsubscribe handles.
- Added isolated health checks and structured result values.
- Retained the complete v0.8.3 QA framework and regression suite.

## 0.8.3 - QA Automation Stabilization

- Added category-filtered runs and test-listing mode.
- Added strict `--fail-on-flaky` support for CI quality gates.
- Corrected JUnit XML error/failure classification and suite metadata.
- Added aggregate coverage summary support and concurrency-safe self-tests.
- Preserved the v0.8.2 Windows SQLite lifecycle fixes and full regression suite.

## 0.8.1 - Debugging and performance

- Added VM breakpoint trace events with instruction-level state snapshots.
- Added deterministic VM profiling with instruction counts and timing metrics.
- Added `debug-vm` and `profile-vm` CLI workflows.
- Added automated coverage for debugger and profiler behavior.

## 0.8.0 - Virtual machine foundation

- Added a stack-based virtual machine and bytecode compiler.
- Added bytecode serialization, execution, and disassembly workflows.
- Added VM-focused CLI commands and automated tests.

## 0.7.1 - Stabilization

- Audited lexer, parser, AST, runtime, diagnostics, and type checker.
- Added stable compiler-component import paths.
- Added diagnostic codes and actionable source diagnostics.
- Added duplicate declaration and top-level return validation.
- Added static unknown-identifier and function-arity checks.
- Added regression tests; complete suite passes with 39 tests.

## Unreleased

- Consolidated ORIEL versions into one open-source repository structure.
- Added architecture, roadmap, CI workflows and contribution guidance.
- Set 0.7.0 bootstrap source as the active engineering baseline.

## 0.7.0

See `versions/0.7.0/README.md` and release assets.
# 0.8.2 - 2026-08-02

- Added `oriel.testing` assertions, snapshots, fixtures, mocks, and parameterized tests.
- Added `oriel.qa` discovery, categorized results, retries, flaky-test detection, and parallel execution.
- Added dependency-free line coverage collection and JUnit XML, HTML, and JSON reports.
- Added polling watch mode and the `oriel-qa` command.
- Added explicit extension interfaces for API, database, web, mobile, performance, security, and AI QA providers.
- Expanded CI to validate QA reports on Python 3.10-3.12 across Linux, Windows, and macOS.
