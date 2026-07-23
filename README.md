# ORIEL Software Language 0.8.1

ORIEL 0.8.1 integrates the package manager, shared language server, VS Code client, serializable IR, bytecode VM, debugger events, profiler and optimization tooling in one repository.


# ORIEL Software Language

**One Language. Infinite Possibilities.**

ORIEL is an experimental open-source programming language and development ecosystem. This repository consolidates the current Python bootstrap implementation, VS Code extension source, tests, examples, architecture documents, historical source snapshots, and release artifacts.

## Current verified baseline

The active codebase in `src/oriel/` is the ORIEL **0.8.1 static type-system implementation**. Historical versions are preserved in `versions/`. Release files are stored in `release-assets/` for convenience; on GitHub they should normally be attached to Releases.

> Status: usable prototype and engineering baseline, not yet a production-stable language.

## Repository map

```text
src/oriel/             Active compiler/interpreter, shared compiler services, CLI and LSP bootstrap
stdlib/                Planned official standard-library modules
frameworks/            Planned API, DB, Web, Desktop, Mobile, Data, AI and Cloud packages
vscode-extension/      VS Code extension source
versions/              Historical source snapshots
release-assets/        Existing wheel, VSIX and source ZIP builds
tests/                 Automated test suites
examples/              Example .orl programs
docs/                  Architecture, language and release documentation
.github/workflows/      CI and release automation
```

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
python -m pytest
oriel version
oriel run examples\hello.orl
```

Linux/macOS activation:

```bash
source .venv/bin/activate
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

## Release policy

A feature is marked implemented only when source code exists, automated tests pass, documentation is updated, and a tagged release can reproduce the published artifacts.

See [Architecture](docs/ARCHITECTURE.md), [Roadmap](docs/ROADMAP.md), and [Contributing](CONTRIBUTING.md).


## ORIEL 0.8.1 static type system and multi-IDE foundation

The compiler frontend is exposed through `oriel.compiler_services.CompilerService`. The LSP consumes this shared API so IDE plugins remain thin. See [Implementation Status](docs/IMPLEMENTATION_STATUS.md) and [IDE Support](docs/IDE_SUPPORT.md).


See [ORIEL 0.8.1 Type System](docs/TYPE_SYSTEM_0.8.1.md) for supported annotations and diagnostics.

## ORIEL 0.8.1 modules

```oriel
use oriel.text
use oriel.math

fn main() {
    print(text_length("ORIEL"))
    print(square(6))
}
```

See `docs/MODULES_AND_STDLIB_0.8.1.md` for module resolution and standard-library details.

## Consolidated repository policy

This is the single ORIEL source repository for the full roadmap. The active implementation is **0.8.1**. Versions 0.1.0–0.7.0 are preserved as historical milestones; versions 0.7.4–0.8.1 are planned and must pass the documented release gates before being marked complete. See `docs/RELEASE_PLAN_0.1.0_TO_0.8.1.md`.


## Consolidated milestone coverage

This single repository preserves ORIEL milestone history from **0.1.0 through 0.8.1**. The active implementation version is **0.8.1**. See `docs/MERGE_STATUS_0.1.0_TO_0.8.1.md` and `docs/VERSION_HISTORY.md`.
