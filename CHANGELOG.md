# Changelog

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
