# ORIEL Engineering Roadmap

## Complete development path: 0.1.0 to 0.8.1

**Current active release: 0.8.1**

This roadmap records the full ORIEL engineering progression from the first language prototype through the consolidated 0.8.1 compiler, tooling, virtual machine, package system, language server, debugger, profiling, and optimization baseline. Historical milestones are preserved under `versions/` where standalone snapshots are available. Continuous releases from 0.7.1 onward are integrated into the active root source tree and documented through tests, changelogs, verification reports, and release notes.

## 0.1.0 — Language foundation

- Initial ORIEL syntax and `.orl` source format
- Basic lexer, parser, interpreter and command-line execution
- Variables, literals, expressions and console output
- Initial examples, tests and installable Python package baseline

## 0.2.0 — Core control flow

- Boolean and comparison expressions
- `if`, `else`, nested conditions and loops
- Improved parser diagnostics and runtime behavior
- Expanded examples and regression tests

## 0.3.0 — Functions and reusable code

- Function declaration and invocation
- Parameters, return values and local scope
- Runtime call-stack improvements
- Function-focused unit and integration tests

## 0.4.0 — Collections and structured data

- Lists, maps and collection operations
- Indexing, iteration and structured values
- Improved error handling for invalid collection access
- Expanded standard-library foundations

## 0.5.0 — Object and module foundations

- Reusable modules and imports
- Encapsulation and structured program organization
- Improved symbol handling and namespace rules
- Multi-file project tests

## 0.6.0 — Tooling and developer workflow

- Improved CLI project, build, run and test commands
- Better diagnostics and source-location reporting
- Initial editor and extension support
- Packaging, examples and documentation improvements

## 0.7.0 — Framework and IDE baseline

- API, database and application-service foundations
- Package-management groundwork
- Initial language-server and VS Code extension source
- Expanded automated tests and historical release package

## 0.7.1 — Compiler stabilization

- Lexer, parser, AST, runtime and diagnostics stabilization
- Shared compiler frontend direction for multiple IDEs
- Regression testing and compatibility verification
- Clearer separation between compiler services and clients

## 0.7.2 — Static type system

- Type annotations, type checking and typed AST support
- Better semantic analysis and compile-time diagnostics
- Type-system verification suite and examples
- Foundation for typed intermediate representation

## 0.7.3 — Modules and standard library

- Module loading, imports and package organization
- Expanded standard-library modules
- Module resolution and integration testing
- Documentation and verification report for the 0.7.3 baseline

## 0.7.4 — Package manager

- `oriel.toml` and deterministic dependency metadata
- Semantic-version resolution and conflict diagnostics
- Local path, Git and registry dependency support
- Checksums, cache, offline workflow and package publishing foundations

## 0.7.5 — Language server and VS Code intelligence

- Shared compiler frontend for editor tooling
- Diagnostics, completion, hover and signature help
- Definition, references, rename and workspace symbols
- Thin VS Code client with reusable LSP architecture

## 0.8.0 — IR, bytecode and virtual machine

- Typed AST to ORIEL intermediate representation
- Optimizer and bytecode generation
- Serializable bytecode format and disassembler
- Stack-based virtual machine with differential tests against the interpreter

## 0.8.1 — Debugger, profiling and consolidated release

- Debugger events, source maps and stack traces
- Breakpoints, stepping and variable inspection foundations
- Profiling, memory reporting and optimization tooling
- Consolidated package manager, LSP, VS Code client, IR, bytecode VM and release documentation
- Verified active source baseline in `src/oriel/`

## Engineering tracks across all releases

### Compiler and runtime

Source management → lexer → parser → AST → semantic analysis → type checker → IR → optimizer → bytecode → VM/runtime.

### Developer experience

CLI, REPL, documentation, examples, testing, Language Server Protocol, Debug Adapter Protocol and thin IDE clients.

### Framework ecosystem

Database, API, web, cross-platform UI, mobile, desktop, data science and AI framework foundations.

### Quality assurance

Every release must include unit tests, integration tests, compatibility checks, security checks, performance validation, documentation updates and reproducible release artifacts.

## Release gate for every version

A version is considered complete only when it includes:

1. Source code and version metadata
2. Automated tests with passing results
3. Updated documentation and changelog
4. Fresh-install and clean-environment verification
5. Reproducible wheel and/or extension artifacts where the preserved source supports them
6. Tagged GitHub release with checksums and release notes

## Next planned stage

The next engineering phase begins after the verified 0.8.1 baseline and should focus on hardening, compatibility, multi-IDE adapters, production-grade package distribution, framework stabilization and the path toward ORIEL 0.9.x and 1.0.0.
