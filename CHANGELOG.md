# Changelog

## 0.7.3 - Modules and Standard Library

### Added
- Deterministic `ModuleGraph`, `ModuleNode` and `ImportSpec` APIs.
- Dotted, relative, aliased and public import parsing.
- Safe project-root containment for relative imports.
- Bundled ORIEL standard-library modules: core, text, math, collections, files, JSON, time, config, logging and testing.
- Module and standard-library unit/integration tests.
- 0.7.3 implementation, architecture and verification documentation.

### Changed
- Python package and VS Code extension versions updated to 0.7.3.
- New projects now depend on `oriel.core` 0.7.3.

### Known limitation
- The bootstrap interpreter still flattens modules; namespace and private-symbol enforcement remain partial until the compiler linker/IR phase.

## 0.7.2 - Static type-system completion

- Added nullable type annotations (`T?`).
- Added typed and nested list annotations (`List[T]`).
- Added homogeneous list inference and index result typing.
- Added mutable assignment and assignment-type validation.
- Added undefined-symbol and duplicate-declaration diagnostics.
- Added function arity and argument-type checking.
- Added boolean-condition and numeric-operator validation.
- Added basic non-null return-path analysis.
- Added public `oriel.type_system` API, documentation, examples and regression tests.
- Updated Python package and VS Code extension versions to 0.7.2.


## 0.7.1 - Stabilization development

- Added a shared compiler-services API for CLI, LSP and future IDE adapters.
- Added structured diagnostics with LSP conversion.
- Routed LSP diagnostics through the shared compiler service.
- Added compiler-service and LSP diagnostic tests.
- Added implementation-status and multi-IDE strategy documents.
- Added placeholder directories for thin IDE adapters.
- Updated project metadata to 0.7.1.

# Changelog

## Unreleased

- Consolidated ORIEL versions into one open-source repository structure.
- Added architecture, roadmap, CI workflows and contribution guidance.
- Set 0.7.0 bootstrap source as the active engineering baseline.

## 0.7.0

See `versions/0.7.0/README.md` and release assets.

## 0.8.1

- Completed the 0.7.4 local/offline package manager foundation.
- Completed the 0.7.5 shared LSP and VS Code language-client foundation.
- Added a serializable ORIEL IR, bytecode compiler and independent stack VM for 0.8.0.
- Added source-line debugging events, profiling, benchmarking and peephole optimization for 0.8.1.
- Added automated package, LSP, VM, debugger and profiler tests.
