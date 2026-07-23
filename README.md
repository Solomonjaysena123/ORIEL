# ORIEL Software Language — Complete Development Repository

## Versions 0.1.0 through 0.8.1

**One Language. Infinite Possibilities.**

ORIEL is an experimental open-source programming language and development ecosystem. This repository brings together the complete documented development path from **ORIEL 0.1.0 to ORIEL 0.8.1**, including historical source snapshots, the current implementation, automated tests, examples, language tooling, the VS Code extension, architecture documentation, and release materials.

> **Current active version:** ORIEL **0.8.1**  
> **Repository coverage:** ORIEL **0.1.0–0.8.1**  
> **Status:** engineering prototype and verified development baseline; not yet production-stable.

## Version coverage

| Version | Main milestone | Repository location/status |
|---|---|---|
| 0.1.0 | Initial CLI and language bootstrap | Historical snapshot in `versions/0.1.0/` |
| 0.2.0 | Core lexer, parser and runtime development | Historical snapshot in `versions/0.2.0/` |
| 0.3.0 | Expanded syntax and test foundation | Historical snapshot in `versions/0.3.0/` |
| 0.4.0 | Runtime and language capability expansion | Historical snapshot in `versions/0.4.0/` |
| 0.5.0 | Framework and tooling foundation | Historical snapshot in `versions/0.5.0/` |
| 0.6.0 | Compiler/runtime stabilization | Historical snapshot in `versions/0.6.0/` |
| 0.7.0 | Integrated bootstrap baseline and VS Code tooling | Historical snapshot in `versions/0.7.0/` |
| 0.7.1 | Shared compiler services, diagnostics and multi-IDE foundation | Integrated into active source and documented in `docs/VERIFICATION_0.7.1.md` |
| 0.7.2 | Static type-system completion | Integrated into active source and documented in `docs/TYPE_SYSTEM_0.7.2.md` |
| 0.7.3 | Module system and standard-library foundation | Integrated into active source and documented in `docs/MODULES_AND_STDLIB_0.7.3.md` |
| 0.7.4 | Local/offline package-manager foundation | Integrated into active source and tests |
| 0.7.5 | Shared LSP and VS Code language-client foundation | Integrated into active source and extension |
| 0.8.0 | Serializable IR, bytecode compiler and stack VM | Integrated into active source and tests |
| 0.8.1 | Debugger events, profiler, optimization and consolidated release | Active implementation in `src/oriel/` |

The `versions/` directory preserves standalone historical snapshots where available. Versions **0.7.1–0.8.1** represent continuous development of the active codebase and are therefore preserved through the root source tree, tests, changelog, and version-specific documentation rather than duplicated full snapshots.

## Current verified baseline — ORIEL 0.8.1

The active implementation in `src/oriel/` contains the consolidated ORIEL 0.8.1 baseline, including:

- lexer, parser, AST and interpreter foundations;
- shared compiler services and structured diagnostics;
- static type-system support;
- module resolution and standard-library integration;
- package-management foundations;
- Language Server Protocol support;
- VS Code extension source;
- serializable intermediate representation;
- bytecode compilation and stack virtual machine;
- debugger events, profiling and optimization tooling;
- automated unit, integration and regression tests.

## Repository structure

```text
src/oriel/             Active ORIEL 0.8.1 compiler, interpreter, CLI, LSP, VM and tooling
versions/              Historical standalone snapshots for 0.1.0–0.7.0
stdlib/                ORIEL standard-library modules
frameworks/            API, database, web, desktop, mobile, data, AI and cloud foundations
vscode-extension/      VS Code extension source and language support
tests/                 Automated tests for the active implementation
examples/              Example ORIEL programs
docs/                  Architecture, version history, verification and release documentation
release-assets/        Existing wheel, VSIX and source-package artifacts
scripts/               Repository verification and maintenance scripts
.github/workflows/      Continuous integration and release automation
```

## Documentation index

- [Complete Version Index](docs/COMPLETE_VERSION_INDEX.md)
- [Complete Version History](docs/VERSION_HISTORY.md)
- [0.1.0–0.8.1 Merge Status](docs/MERGE_STATUS_0.1.0_TO_0.8.1.md)
- [Release Plan](docs/RELEASE_PLAN_0.1.0_TO_0.8.1.md)
- [Implementation Status](docs/IMPLEMENTATION_STATUS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [IDE Support](docs/IDE_SUPPORT.md)
- [Roadmap](docs/ROADMAP.md)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [License](LICENSE)

## Local setup

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
python -m pytest
oriel version
oriel run examples\hello.orl
```

### Linux or macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pytest
oriel version
oriel run examples/hello.orl
```

## Build the Python package

```bash
python -m pip install build
python -m build
```

## Build the VS Code extension

```bash
cd vscode-extension
npm install
npx @vscode/vsce package
```

## Verify the repository

```bash
python scripts/verify_repository.py
python -m pytest
```

## Release and development policy

A version or feature is considered implemented only when:

1. source code is present;
2. automated tests pass;
3. documentation and the changelog are updated;
4. version metadata is consistent;
5. release artifacts can be reproduced from a tagged commit.

Historical snapshots are retained for traceability. New development continues in the active root codebase and should be released through Git tags and GitHub Releases rather than by duplicating the entire repository for each patch version.

## License

See [LICENSE](LICENSE) for the repository license terms.

## Packaged release artifacts

Verified Python wheels are stored in `release-assets/` for preserved source snapshots: **0.1.0–0.7.0 and 0.8.1**. The current **0.8.1 VS Code extension** is included as a `.vsix` package.

Versions **0.7.1–0.8.0** are represented in the integrated changelog, but exact standalone source snapshots were not preserved; binary packages for those versions are intentionally not fabricated. See [`docs/RELEASE_ARTIFACT_MATRIX.md`](docs/RELEASE_ARTIFACT_MATRIX.md).
