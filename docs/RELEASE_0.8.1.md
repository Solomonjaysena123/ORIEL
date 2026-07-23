# ORIEL 0.8.1 Release Report

## Included milestones

### 0.7.4 Package Manager
- `oriel add`, `remove`, `install`, `packages` and `publish`
- Semantic constraints (`>=`, `^`, `~`, exact and latest)
- Transitive dependency resolution and conflict detection
- `oriel.lock` with stable checksums
- Local path dependencies
- Local package archive and registry index
- Offline package cache

### 0.7.5 Language Server and VS Code
- Shared compiler-powered diagnostics
- Completion, hover, definition, references, rename and document symbols
- JSON-RPC/LSP over standard input/output
- VS Code extension using `vscode-languageclient`

### 0.8.0 Compiler, IR, Bytecode and VM
- AST-to-IR compiler
- Versioned serializable `.obc` format
- Stack virtual machine
- Functions, variables, arithmetic, comparisons, control flow, loops, lists and indexing
- Bytecode validation and round-trip tests

### 0.8.1 Debugger, Profiler and Optimization
- Source-line breakpoint events
- Local-variable snapshots
- Instruction-count profiler
- VM/interpreter benchmark selection
- Conservative peephole optimization

## Verification

- Automated tests: **54 passed**
- Python source compilation: **passed**
- CLI version: **Oriel 0.8.1**
- Optimized bytecode compilation: **passed**
- VM execution of `examples/hello.orl`: **passed**
- Profiler smoke test: **passed**
