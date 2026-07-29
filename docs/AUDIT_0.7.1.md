# ORIEL 0.7.1 Stabilization Audit

## Scope

This audit covers the bootstrap console implementation's lexer, parser, AST,
runtime, diagnostics, and initial type checker.

## Stabilized in 0.7.1

- Added stable public module paths: `oriel.lexer`, `oriel.parser`, `oriel.ast`,
  `oriel.runtime`, `oriel.diagnostics`, and `oriel.typechecker`.
- Added stage-specific diagnostic codes for lexer, parser, name resolution,
  type checking, and runtime failures.
- Improved diagnostic rendering with source ranges and actionable help text.
- Rejected duplicate declarations in the same runtime scope.
- Rejected `return` statements outside functions with a structured diagnostic.
- Added static unknown-identifier detection.
- Added static user-function arity checking.
- Added structured division/modulo-by-zero diagnostics.
- Added focused regression tests for token positions, AST shape, parser failures,
  runtime scoping, top-level return, identifiers, and function calls.

## Verification

- Full automated suite: **39 passed**.
- Existing integration tests remain compatible.
- Version metadata updated to `0.7.1`.

## Known limitations

- The implementation remains a Python bootstrap interpreter.
- Compiler components are exposed through separate public modules, but their
  internal implementation still lives in the compatibility module
  `oriel.interpreter`. A later release should physically separate internals.
- Parser error recovery is not incremental; parsing stops on the first error.
- Generic types, user-defined structs/classes, nullable types, and Result-based
  error handling are not complete.
- The language server requires further workspace indexing and semantic features.

## Release decision

ORIEL 0.7.1 is suitable as a stabilization development release. It should not
be described as a production-grade 1.0 language.
