# ORIEL Consolidated Release Plan: 0.1.0 to 0.8.1

This repository is the single active ORIEL source repository. Historical milestones are recorded under `versions/` and in the version history. The active implementation is ORIEL 0.7.3. Later milestones remain planned until their completion gates pass.

## Release matrix

| Version | Milestone | Phase | Status | Mandatory quality gate |
|---|---|---|---|---|
| 0.1.0 | Initial console interpreter | Prototype | Historical | Tests + docs + CI + tagged artifacts |
| 0.2.0 | Collections, loops, files and JSON | Prototype | Historical | Tests + docs + CI + tagged artifacts |
| 0.3.0 | Diagnostics, typing and package foundations | Foundation | Historical | Tests + docs + CI + tagged artifacts |
| 0.4.0 | Modules, language intelligence and API preview | Foundation | Historical | Tests + docs + CI + tagged artifacts |
| 0.5.0 | Database preview and OpenAPI | Foundation | Historical | Tests + docs + CI + tagged artifacts |
| 0.6.0 | Application services, validation and authentication utilities | Foundation | Historical | Tests + docs + CI + tagged artifacts |
| 0.7.0 | Initial console foundation | Foundation | Historical baseline | Tests + docs + CI + tagged artifacts |
| 0.7.1 | Core audit and stabilization | Stabilization | Completed in consolidated source | Tests + docs + CI + tagged artifacts |
| 0.7.2 | Static type-system completion | Stabilization | Completed in consolidated source | Tests + docs + CI + tagged artifacts |
| 0.7.3 | Modules and standard library | Stabilization | Current active release | Tests + docs + CI + tagged artifacts |
| 0.7.4 | Package manager | Stabilization | Planned | Tests + docs + CI + tagged artifacts |
| 0.7.5 | Language server and VS Code intelligence | Stabilization | Planned | Tests + docs + CI + tagged artifacts |
| 0.8.0 | Compiler, IR, bytecode and virtual machine | Compiler | Planned | Tests + docs + CI + tagged artifacts |
| 0.8.1 | Debugger, profiling and optimization | Compiler | Planned | Tests + docs + CI + tagged artifacts |

## Repository policy

- `main` contains stable tagged releases.
- `develop` contains current integration work.
- `feature/*` contains individual features.
- `fix/*` contains isolated corrections.
- Historical releases must not be maintained as separate source repositories.
- Build outputs such as `.whl`, `.vsix`, generated archives and test caches must not be committed to normal source folders.

## Completion definition

A milestone is complete only when all of the following are true:

1. Source code exists in this repository.
2. Automated tests exist for the feature.
3. All tests pass on Windows, Ubuntu and macOS where applicable.
4. User and developer documentation exists.
5. A fresh-clone installation succeeds.
6. CI builds reproducible release artifacts.
7. The tagged commit contains exactly the released implementation.

## Next implementation sequence

### 0.7.4 Package manager

- `oriel.toml` and deterministic `oriel.lock`
- Semantic-version and dependency resolution
- Local path, Git and registry dependencies
- Checksums, cache and offline installation
- Package publishing workflow and local CI registry

### 0.7.5 Shared language intelligence

- Shared compiler-service API
- LSP diagnostics, completion, hover and signature help
- Definition, references, rename, symbols and semantic tokens
- Formatting, code actions and import completion
- Thin VS Code extension and reusable adapters for other IDEs

### 0.8.0 Compiler, IR and VM

- Typed AST to ORIEL IR lowering
- Versioned bytecode format
- Stack-based virtual machine
- Modules, frames, constants and serialization
- Differential interpreter-versus-VM tests

### 0.8.1 Debugger and performance tooling

- Debug source maps and stack traces
- Breakpoints and step controls through DAP
- Variable inspection and watch expressions
- Profiler, benchmark reports and regression thresholds
- Debug and release build modes
