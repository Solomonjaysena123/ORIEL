# Changelog

## 0.9.3 - Authentication and Security Framework

- Added configurable PBKDF2-SHA256 password hashing, verification, and rehash policy.
- Added versioned HMAC-SHA256 authentication tokens with issuer, audience, expiry, roles, permissions, and unique IDs.
- Added thread-safe expiring sessions, revocation, permission enforcement, CSRF tokens, and rate limiting.
- Added secure web response headers through the v0.9.2 middleware pipeline.
- Added tampering, expiry, session, CSRF, authorization, throttling, and header regression tests.

## 0.9.2 - Server-Rendered Web Framework

- Added dependency-free web requests, responses, dynamic routing, redirects, and middleware.
- Added code-free HTML templates with context escaping and root-path confinement.
- Added static-file MIME detection, `nosniff` protection, and traversal containment.
- Added an in-process web test client and method-aware 404/405 behavior.
- Added security, middleware, template, routing, and static-file regression tests.

## 0.9.1 - Database Application Framework

- Added idempotent, SHA-256 identified SQLite migrations and auditable migration history.
- Added duplicate entity and field validation for ORIEL schemas.
- Added explicit commit/rollback transaction sessions and parameterized query helpers.
- Added database health checks and the `oriel db status` CLI workflow.
- Updated database project scaffolding and added transaction/migration regression tests.

## 0.9.0 - Shared Application Framework Kernel

- Added deterministic application lifecycle management and reverse-order shutdown hooks.
- Added immutable environment configuration with required-value validation.
- Added thread-safe singleton/transient service resolution and circular-dependency detection.
- Added synchronous event publishing with unsubscribe support.
- Added isolated health checks and structured success/error results.

## 0.8.3 - QA Automation Stabilization

- Added category-filtered runs and test-listing mode.
- Added strict `--fail-on-flaky` support for CI quality gates.
- Corrected JUnit XML error/failure classification and suite metadata.
- Added aggregate coverage summary support and concurrency-safe self-tests.
- Expanded regression tests for filtering, CLI discovery, and report validity.

## 0.8.2 - QA Automation Framework

- Added `oriel.testing` assertions, snapshots, fixtures, mocks, and parameterized tests.
- Added `oriel.qa` discovery, categorized results, retries, flaky-test detection, and parallel execution.
- Added dependency-free line coverage collection and JUnit XML, HTML, and JSON reports.
- Added polling watch mode and the `oriel-qa` command.
- Added extension interfaces for API, database, web, mobile, performance, security, and AI QA providers.
- Expanded CI to validate QA reports on Python 3.10-3.12 across Linux, Windows, and macOS.

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
