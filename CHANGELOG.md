# Changelog

## 0.7.3 - Modules and standard library

- Added deterministic multi-file module graph resolution.
- Added circular import detection with readable dependency paths.
- Added a registry for core, text, math, collections, files, JSON, time, configuration, logging, and testing standard modules.
- Added package dependency resolution and reproducible lock-file metadata.
- Added module and standard-library regression coverage.

## 0.7.2 - Static type-system foundation

- Added primitive, collection, nullable, generic, and function type models.
- Added nested type parsing, literal inference, assignment compatibility, common-type resolution, and numeric widening.
- Added focused type-system regression coverage.

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
