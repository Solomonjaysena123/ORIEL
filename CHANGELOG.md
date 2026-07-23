# ORIEL Changelog

This changelog records the consolidated ORIEL development path from **0.1.0 through 0.8.1**.

## 0.8.1 — Debugging, profiling and optimization

- Added source-line debugger events.
- Added profiling and benchmarking support.
- Added peephole optimization tooling.
- Consolidated the active compiler, VM, LSP, package and IDE foundations.
- Added automated debugger and profiler tests.

## 0.8.0 — Intermediate representation and bytecode VM

- Added a serializable ORIEL intermediate representation.
- Added bytecode compilation.
- Added an independent stack virtual machine.
- Added VM and bytecode regression tests.

## 0.7.5 — Shared LSP and VS Code client foundation

- Added shared language-server foundations.
- Expanded VS Code language-client integration.
- Preserved thin-client architecture for future IDE adapters.
- Added LSP and client integration tests.

## 0.7.4 — Package-manager foundation

- Added local and offline package-management foundations.
- Added package metadata and package-resolution support.
- Added automated package tests.

## 0.7.3 — Modules and standard library

- Added deterministic `ModuleGraph`, `ModuleNode` and `ImportSpec` APIs.
- Added dotted, relative, aliased and public import parsing.
- Added safe project-root containment for relative imports.
- Added bundled standard-library modules for core, text, math, collections, files, JSON, time, config, logging and testing.
- Added module and standard-library unit/integration tests.
- Added implementation, architecture and verification documentation.

### Known limitation

- The bootstrap interpreter still flattens modules; complete namespace and private-symbol enforcement remains part of later compiler/linker work.

## 0.7.2 — Static type-system completion

- Added nullable type annotations (`T?`).
- Added typed and nested list annotations (`List[T]`).
- Added homogeneous list inference and index result typing.
- Added mutable assignment and assignment-type validation.
- Added undefined-symbol and duplicate-declaration diagnostics.
- Added function arity and argument-type checking.
- Added boolean-condition and numeric-operator validation.
- Added basic non-null return-path analysis.
- Added public type-system APIs, documentation, examples and regression tests.

## 0.7.1 — Stabilization and multi-IDE foundation

- Added a shared compiler-services API for CLI, LSP and future IDE adapters.
- Added structured diagnostics with LSP conversion.
- Routed LSP diagnostics through the shared compiler service.
- Added compiler-service and LSP diagnostic tests.
- Added implementation-status and multi-IDE strategy documents.
- Added placeholder directories for thin IDE adapters.

## 0.7.0 — Integrated bootstrap baseline

- Established the consolidated bootstrap source baseline.
- Added language tooling and VS Code extension foundations.
- Preserved the standalone snapshot in `versions/0.7.0/`.

## 0.6.0

- Continued compiler/runtime stabilization.
- Expanded tests and engineering structure.
- Preserved the standalone snapshot in `versions/0.6.0/`.

## 0.5.0

- Expanded framework and developer-tooling foundations.
- Preserved the standalone snapshot in `versions/0.5.0/`.

## 0.4.0

- Expanded runtime and language capabilities.
- Preserved the standalone snapshot in `versions/0.4.0/`.

## 0.3.0

- Expanded syntax, implementation structure and tests.
- Preserved the standalone snapshot in `versions/0.3.0/`.

## 0.2.0

- Developed the core lexer, parser and runtime foundation.
- Preserved the standalone snapshot in `versions/0.2.0/`.

## 0.1.0 — Initial bootstrap

- Introduced the initial ORIEL command-line and language bootstrap package.
- Preserved the initial package in `versions/0.1.0/`.
