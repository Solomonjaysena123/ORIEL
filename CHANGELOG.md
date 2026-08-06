# Changelog

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
