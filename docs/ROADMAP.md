# ORIEL Engineering Roadmap

## Current release: 0.7.3

The repository currently integrates the 0.7.1 stabilization work, 0.7.2 static type-system work and 0.7.3 modules/standard-library work. Versions 0.1.0–0.7.0 are historical milestones. Planned work must not be presented as implemented.

## 0.7.4 — Package manager

- `oriel.toml` and deterministic `oriel.lock`
- Semantic-version resolution and conflict diagnostics
- Local path, Git and registry dependencies
- Checksums, cache, offline mode and package publishing
- Resolver, lock-file and corruption tests

## 0.7.5 — Language server and VS Code intelligence

- Shared compiler frontend for all editors
- Diagnostics, completion, hover and signature help
- Definition, references, rename and workspace symbols
- Semantic highlighting, formatting, code actions and imports
- Thin VS Code client plus reusable LSP setup for supported IDEs

## 0.8.0 — Compiler, IR, bytecode and VM

- Typed AST to ORIEL IR
- Bytecode compiler and versioned `.obc` format
- Stack-based VM with functions, constants and modules
- Serialization, disassembler and invalid-bytecode rejection
- Differential tests against the interpreter

## 0.8.1 — Debugger, profiling and optimization

- Source maps, stack traces and breakpoints
- Step in, step over, step out and variable inspection
- DAP integration for supported IDEs
- Profiling, memory reports and performance thresholds
- Debug and release build modes

## Release gate for every version

Source code + automated tests + passing CI + documentation + fresh-install verification + tagged reproducible artifacts.
